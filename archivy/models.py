from datetime import datetime
from pkg_resources import require
from typing import List, Optional
from urllib.parse import urljoin
from io import BytesIO
import fnmatch

import frontmatter
import requests
import validators
from attr import attrs, attrib
from attr.validators import instance_of, optional
from bs4 import BeautifulSoup
from flask import flash, current_app
from flask_login import UserMixin
from html2text import html2text
from tinydb import Query
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage

from archivy import helpers
from archivy.data import create, save_image, valid_image_filename
from archivy.search import add_to_index
from archivy.tags import add_tag_to_index


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

    id: Optional[int] = attrib(validator=optional(instance_of(int)), default=None)
    type: str = attrib(validator=instance_of(str))
    title: str = attrib(validator=instance_of(str), default="")
    content: str = attrib(validator=instance_of(str), default="")
    tags: List[str] = attrib(validator=instance_of(list), default=[])
    url: Optional[str] = attrib(validator=optional(instance_of(str)), default=None)
    date: Optional[datetime] = attrib(
        validator=optional(instance_of(datetime)), default=None
    )
    path: str = attrib(validator=instance_of(str), default="")
    fullpath: Optional[str] = attrib(validator=optional(instance_of(str)), default=None)
    error: Optional[str] = attrib(validator=optional(instance_of(str)), default=None)

    def process_bookmark_url(self):
        """Process url to get content for bookmark"""
        if self.type not in ("bookmark", "pocket_bookmark") or not validators.url(
            self.url
        ):
            return None
        selector = None
        for pattern, handler in current_app.config["SCRAPING_PATTERNS"].items():
            if fnmatch.fnmatch(self.url, pattern):
                if type(handler) == str:
                    # if the handler is a string, it's simply a css selector to process the page with
                    selector = handler
                    break
                # otherwise custom user function that overrides archivy behavior
                handler(self)
                return

        try:
            url_request = requests.get(
                self.url,
                headers={"User-agent": f"Archivy/v{require('archivy')[0].version}"},
            )
        except Exception:
            self.error = f"Could not retrieve {self.url}\n"
            self.wipe()
            return

        try:
            parsed_html = BeautifulSoup(url_request.text, features="html.parser")
        except Exception:
            self.error = f"Could not parse {self.url}\n"
            self.wipe()
            return

        try:
            self.content = self.extract_content(parsed_html, selector)
        except Exception:
            self.error = f"Could not extract content from {self.url}\n"
            return

        parsed_title = parsed_html.title
        self.title = parsed_title.string if parsed_title is not None else self.url

    def wipe(self):
        """Resets and invalidates dataobj"""
        self.title = ""
        self.content = ""

    def extract_content(self, beautsoup, selector=None):
        """converts html bookmark url to optimized markdown and saves images"""

        stripped_tags = ["footer", "nav"]
        url = self.url.rstrip("/")

        if selector:
            selected_soup = beautsoup.select(selector)
            # if the custom selector matched, take the first occurrence
            if selected_soup:
                beautsoup = selected_soup[0]
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

            elif tag.name == "img" and tag.has_attr("src"):
                filename = tag["src"].split("/")[-1]
                try:
                    filename = filename[
                        : filename.index("?")
                    ]  # remove query parameters
                except ValueError:
                    pass
                if not tag["src"].startswith("http"):
                    tag["src"] = urljoin(url, tag["src"])
                if current_app.config["SCRAPING_CONF"][
                    "save_images"
                ] and valid_image_filename(filename):
                    image = FileStorage(
                        BytesIO(requests.get(tag["src"]).content), filename, name="file"
                    )
                    saved_to = save_image(image)
                    tag["src"] = "/images/" + saved_to

        res = html2text(str(beautsoup), bodywidth=0)
        return res

    def validate(self):
        """Verifies that the content matches required validation constraints"""
        valid_url = (self.type != "bookmark" or self.type != "pocket_bookmark") or (
            isinstance(self.url, str) and validators.url(self.url)
        )

        valid_title = isinstance(self.title, str) and self.title != ""
        valid_content = self.type not in ("bookmark", "pocket_bookmark") or isinstance(
            self.content, str
        )
        return valid_url and valid_title and valid_content

    def insert(self):
        """Creates a new file with the object's attributes"""
        if self.validate():
            for tag in self.tags:
                add_tag_to_index(tag)
            helpers.set_max_id(helpers.get_max_id() + 1)
            self.id = helpers.get_max_id()
            self.date = datetime.now()

            hooks = current_app.config["HOOKS"]

            hooks.before_dataobj_create(self)
            data = {
                "type": self.type,
                "title": str(self.title),
                "date": self.date.strftime("%x").replace("/", "-"),
                "tags": self.tags,
                "id": self.id,
                "path": self.path,
            }
            if self.type == "bookmark" or self.type == "pocket_bookmark":
                data["url"] = self.url

            # convert to markdown file
            dataobj = frontmatter.Post(self.content)
            dataobj.metadata = data
            self.fullpath = str(
                create(
                    frontmatter.dumps(dataobj),
                    f"{self.id}-{dataobj['title']}",
                    path=self.path,
                )
            )

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
        for pair in ["id", "title", "path", "tags"]:
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
    is_admin: Optional[bool] = attrib(
        validator=optional(instance_of(bool)), default=None
    )
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
            "type": "user",
        }

        current_app.config["HOOKS"].on_user_create(self)
        return db.insert(db_user)

    @classmethod
    def from_db(cls, db_object):
        """Takes a database object and turns it into a user"""
        username = db_object["username"]
        id = db_object.doc_id

        return cls(username=username, id=id)
