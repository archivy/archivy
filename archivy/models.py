from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import frontmatter
from pypandoc import convert_text
import requests
import validators
from attr import attrs, attrib
from attr.validators import instance_of, optional
from bs4 import BeautifulSoup
from flask import current_app, flash
from flask_login import UserMixin
from tinydb import Query
from werkzeug.security import generate_password_hash

from archivy import extensions
from archivy.data import create
from archivy.search import add_to_index


# TODO: use this as 'type' field
# class DataobjType(Enum):
#     BOOKMARK = 'bookmark'
#     POCKET_BOOKMARK = 'bookmark imported from pocket'
#     NOTE = 'note'
#     PROCESSED_DATAOBJ = 'bookmark that has been processed'

# TODO: use this as 'type' field
# class DataobjType(Enum):
#     BOOKMARK = 'bookmark'
#     POCKET_BOOKMARK = 'bookmark imported from pocket'
#     NOTE = 'note'
#     PROCESSED_DATAOBJ = 'bookmark that has been processed'

@attrs(kw_only=True)
class DataObj:
    __searchable__ = ["title", "content", "desc", "tags"]

    id: Optional[int] = attrib(validator=optional(instance_of(int)),
                               default=None)
    type: str = attrib(validator=instance_of(str))
    title: str = attrib(validator=instance_of(str), default="")
    content: str = attrib(validator=instance_of(str), default="")
    desc: Optional[str] = attrib(validator=optional(instance_of(str)),
                                 default=None)
    tags: List[str] = attrib(validator=instance_of(list), default=[])
    url: Optional[str] = attrib(validator=optional(instance_of(str)),
                                default=None)
    date: Optional[datetime] = attrib(
        validator=optional(instance_of(datetime)),
        default=None,
    )
    path: str = attrib(validator=instance_of(str), default="")
    fullpath: Optional[str] = attrib(validator=optional(instance_of(str)),
                                     default=None)

    def process_bookmark_url(self):
        """Process url to get content for bookmark"""
        if self.type not in ("bookmarks", "pocket_bookmarks") or not validators.url(self.url):
            return None

        try:
            url_request = requests.get(self.url)
        except Exception:
            flash(f"Could not retrieve {self.url}\n")
            self.wipe()
            return

        try:
            parsed_html = BeautifulSoup(url_request.text,
                                        features="html.parser")
        except Exception:
            flash(f"Could not parse {self.url}\n")
            self.wipe()
            return

        try:
            self.content = self.extract_content(parsed_html)
        except Exception:
            flash(f"Could not extract content from {self.url}\n")
            return

        parsed_title = parsed_html.title
        self.title = (parsed_title.string if parsed_title is not None
                      else self.url)

    def wipe(self):
        """Resets and invalidates dataobj"""
        self.title = ""
        self.desc = None
        self.content = ""

    def extract_content(self, beautsoup):
        """converts html bookmark url to optimized markdown"""

        stripped_tags = ["footer", "nav"]
        url = self.url.rstrip("/")

        for tag in stripped_tags:
            if getattr(beautsoup, tag):
                getattr(beautsoup, tag).extract()
        resources = beautsoup.find_all(["a", "img"])
        for external in resources:
            if external.name == "a" and \
                    external.has_attr("href") and \
                    external["href"].startswith("/"):
                external["href"] = urljoin(url, external["href"])
            elif external.name == "img" and \
                    external.has_attr("src") and \
                    external["src"].startswith("/"):
                external["src"] = urljoin(url, external["src"])

        return convert_text(str(beautsoup), "md", format="html")

    def validate(self):
        valid_url = (self.type != "bookmarks" or self.type != "pocket_bookmarks") or (
                    isinstance(self.url, str) and validators.url(self.url))

        valid_title = isinstance(self.title, str) and self.title != ""
        valid_content = (self.type not in ("bookmark", "pocket_bookmarks")
                         or isinstance(self.content, str))
        return valid_url and valid_title and valid_content

    def insert(self):
        if self.validate():
            extensions.set_max_id(extensions.get_max_id() + 1)
            self.id = extensions.get_max_id()
            self.date = datetime.now()
            data = {
                "type": self.type,
                "desc": self.desc,
                "title": str(self.title),
                "date": self.date.strftime("%x").replace("/", "-"),
                "tags": self.tags,
                "id": self.id,
                "path": self.path
            }
            if self.type == "bookmarks" or self.type == "pocket_bookmarks":
                data["url"] = self.url

            # convert to markdown file
            dataobj = frontmatter.Post(self.content)
            dataobj.metadata = data
            self.fullpath = create(
                                frontmatter.dumps(dataobj),
                                str(self.id) + "-" +
                                dataobj["date"] + "-" + dataobj["title"],
                                path=self.path,
                                )

            add_to_index(current_app.config['INDEX_NAME'], self)
            return self.id
        return False

    @classmethod
    def from_file(cls, filename):
        data = frontmatter.load(filename)
        dataobj = {}
        dataobj["content"] = data.content
        for pair in ["tags", "desc", "id", "title", "path"]:
            try:
                dataobj[pair] = data[pair]
            except KeyError:
                # files sometimes get moved temporarily by applications while you edit
                # this can create bugs where the data is not loaded correctly
                # this handles that scenario as validation will simply fail and the event will
                # be ignored
                break

        dataobj["type"] = "processed-dataobj"
        return cls(**dataobj)


@attrs(kw_only=True)
class User(UserMixin):
    username: str = attrib(validator=instance_of(str))
    password: Optional[str] = attrib(validator=optional(instance_of(str)), default=None)
    is_admin: Optional[bool] = attrib(validator=optional(instance_of(bool)), default=None)
    id: Optional[int] = attrib(validator=optional(instance_of(int)), default=False)

    def insert(self):

        if not self.password:
            return False

        hashed_password = generate_password_hash(self.password)
        db = extensions.get_db()

        if db.search((Query().type == "user") & (Query().username == self.username)):
            return False
        db_user = {
            "username": self.username,
            "hashed_password": hashed_password,
            "is_admin": self.is_admin,
            "type": "user"
        }

        return db.insert(db_user)

    @classmethod
    def from_db(cls, db_object):

        username = db_object["username"]
        id = db_object.doc_id

        return cls(username=username, id=id)
