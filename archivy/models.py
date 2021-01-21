from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import frontmatter
import requests
import validators
from attr import attrs, attrib
from attr.validators import instance_of, optional
from bs4 import BeautifulSoup
from flask import flash
from flask_login import UserMixin
from html2text import html2text
from tinydb import Query
from werkzeug.security import generate_password_hash

from archivy import helpers
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
    """
    Class that holds a data object (either a note or a bookmark).

    Attributes:

    [Required to pass when creating a new object]

    - **type** -> "note" or "bookmark"

     **Note**:
    - title

    **Bookmark**:

    - url

    [Optional attrs that if passed, will be set by the class]

    - tags
    - content
    - path

    [Handled by the code]

    - id
    - date

    For bookmarks,
    Run `process_bookmark_url()` once you've created it.

    For both types, run `insert()` if you want to create a new file in
    the db with their contents.
    """

    __searchable__ = ["title", "content", "tags"]

    id: Optional[int] = attrib(validator=optional(instance_of(int)),
                               default=None)
    type: str = attrib(validator=instance_of(str))
    title: str = attrib(validator=instance_of(str), default="")
    content: str = attrib(validator=instance_of(str), default="")
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
        if self.type not in ("bookmark", "pocket_bookmark") or not validators.url(self.url):
            return None

        try:
            url_request = requests.get(self.url)
        except Exception:
            flash(f"Could not retrieve {self.url}\n", "error")
            self.wipe()
            return

        try:
            parsed_html = BeautifulSoup(url_request.text,
                                        features="html.parser")
        except Exception:
            flash(f"Could not parse {self.url}\n", "error")
            self.wipe()
            return

        try:
            self.content = self.extract_content(parsed_html)
        except Exception:
            flash(f"Could not extract content from {self.url}\n", "error")
            return

        parsed_title = parsed_html.title
        self.title = (parsed_title.string if parsed_title is not None
                      else self.url)

    def wipe(self):
        """Resets and invalidates dataobj"""
        self.title = ""
        self.content = ""

    def extract_content(self, beautsoup):
        """converts html bookmark url to optimized markdown"""

        stripped_tags = ["footer", "nav"]
        url = self.url.rstrip("/")

        for tag in stripped_tags:
            if getattr(beautsoup, tag):
                getattr(beautsoup, tag).extract()
        resources = beautsoup.find_all(["a", "img"])
        for tag in resources:
            if tag.name == "a":
                if tag.has_attr("href") and (tag["href"].startswith("/")):
                    tag["href"] = urljoin(url, tag["href"])

                # check it's a normal link and not some sort of image
                # string returns the text content of the tag
                if not tag.string:
                    # delete tag
                    tag.decompose()

            elif tag.name == "img" and tag.has_attr("src") and (tag["src"].startswith("/")
                                                                or tag["src"].startswith("./")):

                tag["src"] = urljoin(url, tag["src"])

        res = html2text(str(beautsoup), bodywidth=0)
        return res

    def validate(self):
        """Verifies that the content matches required validation constraints"""
        valid_url = (self.type != "bookmark" or self.type != "pocket_bookmark") or (
                    isinstance(self.url, str) and validators.url(self.url))

        valid_title = isinstance(self.title, str) and self.title != ""
        valid_content = (self.type not in ("bookmark", "pocket_bookmark")
                         or isinstance(self.content, str))
        return valid_url and valid_title and valid_content

    def insert(self):
        """Creates a new file with the object's attributes"""
        if self.validate():

            helpers.set_max_id(helpers.get_max_id() + 1)
            self.id = helpers.get_max_id()
            self.date = datetime.now()

            hooks = helpers.load_hooks()

            hooks.before_dataobj_create(self)
            data = {
                "type": self.type,
                "title": str(self.title),
                "date": self.date.strftime("%x").replace("/", "-"),
                "tags": self.tags,
                "id": self.id,
                "path": self.path
            }
            if self.type == "bookmark" or self.type == "pocket_bookmark":
                data["url"] = self.url

            # convert to markdown file
            dataobj = frontmatter.Post(self.content)
            dataobj.metadata = data
            self.fullpath = str(create(
                                    frontmatter.dumps(dataobj),
                                    f"{self.id}-{dataobj['title']}",
                                    path=self.path,
                                ))

            hooks.on_dataobj_create(self)
            self.index()
            return self.id
        return False

    def index(self):
        return add_to_index(self)

    @classmethod
    def from_md(cls, md_content: str):
        """
        Class method to generate new dataobj from a well formatted markdown string

        Call like this:

        ```python
        Dataobj.from_md(content)

        ```
        """
        data = frontmatter.loads(md_content)
        dataobj = {}
        dataobj["content"] = data.content
        for pair in ["tags", "id", "title", "path"]:
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
    """
    Model we use for User that inherits from flask login's
    [`UserMixin`](https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin)

    Attributes:

    - **username**
    - **password**
    - **is_admin**
    """

    username: str = attrib(validator=instance_of(str))
    password: Optional[str] = attrib(validator=optional(instance_of(str)), default=None)
    is_admin: Optional[bool] = attrib(validator=optional(instance_of(bool)), default=None)
    id: Optional[int] = attrib(validator=optional(instance_of(int)), default=False)

    def insert(self):
        """Inserts the model from the database"""
        if not self.password:
            return False

        hashed_password = generate_password_hash(self.password)
        db = helpers.get_db()

        if db.search((Query().type == "user") & (Query().username == self.username)):
            return False
        db_user = {
            "username": self.username,
            "hashed_password": hashed_password,
            "is_admin": self.is_admin,
            "type": "user"
        }

        helpers.load_hooks().on_user_create(self)
        return db.insert(db_user)

    @classmethod
    def from_db(cls, db_object):
        """Takes a database object and turns it into a user"""
        username = db_object["username"]
        id = db_object.doc_id

        return cls(username=username, id=id)
