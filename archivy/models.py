import datetime
from urllib.parse import urljoin

import validators
import requests
import html2text
import frontmatter
from flask import flash
from bs4 import BeautifulSoup
from flask import current_app

from archivy import extensions
from archivy.search import add_to_index
from archivy.data import create


class DataObj:
    __searchable__ = ["title", "content", "desc", "tags"]

    def process_bookmark_url(self):
        try:
            url_request = requests.get(self.url).text
        except Exception:
            flash(f"Could not retrieve {self.url}\n")
            self.wipe()
            return
        try:
            parsed_html = BeautifulSoup(url_request, features="html.parser")
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
        self.title = None
        self.desc = None
        self.content = None

    def extract_content(self, beautsoup):
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

        return html2text.html2text(str(beautsoup))

    def __init__(self, **kwargs):

        # data has already been processed
        if kwargs["type"] == "processed-dataobj":
            for key, value in kwargs.items():
                setattr(self, key, value)
        else:
            # still needs processing

            if "path" not in kwargs or kwargs["path"] == "not classified":
                kwargs["path"] = ""

            # set_attributes (path, desc, tags, type, title)
            self.path = kwargs["path"]
            self.desc = kwargs.get("desc") or ""
            self.tags = kwargs.get("tags") or []
            self.type = kwargs["type"]
            self.title = kwargs.get("title") or ""

            self.date = datetime.datetime.now()
            self.content = kwargs.get("content") or ""
            self.fullpath = ""
            self.id = None
            if self.type == "bookmarks" or self.type == "pocket_bookmarks":
                self.url = kwargs["url"]
                if validators.url(self.url):
                    self.process_bookmark_url()

    def validate(self):
        valid_url = (
            self.type != "bookmarks" or self.type != "pocket_bookmarks") or (
            isinstance(
                self.url,
                str) and validators.url(
                self.url))
        valid_title = isinstance(self.title, str)
        valid_content = (self.type != "bookmark" and
                         self.type != "pocket_bookmarks") or \
            isinstance(self.content, str)
        return valid_url and valid_title and valid_content

    def insert(self):
        if self.validate():
            extensions.set_max_id(extensions.get_max_id() + 1)
            self.id = extensions.get_max_id()
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

            # convert to markdown
            dataobj = frontmatter.Post(self.content)
            dataobj.metadata = data
            self.fullpath = create(
                                frontmatter.dumps(dataobj),
                                str(self.id) + "-" +
                                dataobj["date"] + "-" + dataobj["title"],
                                path=self.path,
                                needs_to_open=self.type == "note")

            add_to_index(current_app.config['INDEX_NAME'], self)
            return self.id
        return False

    @classmethod
    def from_file(cls, filename):
        data = frontmatter.load(filename)
        dataobj = {}
        dataobj["content"] = data.content
        for pair in ["tags", "desc", "id", "title", "path"]:
            dataobj[pair] = data[pair]

        dataobj["type"] = "processed-dataobj"
        return cls(**dataobj)
