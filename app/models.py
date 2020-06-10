import validators
from app import db
import requests
import html2text
from bs4 import BeautifulSoup
import re
import datetime
from app.search import *

class Bookmark:
    __searchable__ = ['title', 'content', 'desc', 'tags']
    def wipe(self):
        self.title = None
        self.desc = None
        self.content = None

    def from_json(self, data):
        self.url = data["url"]
        self.title = data["title"]
        self.content = data["content"]
        self.desc = data["desc"]
        self.date = data["date"]

    def extract_content(self, beautsoup):
        stripped_tags = ['footer', 'nav']
        for x in stripped_tags:
            if getattr(beautsoup, x):
                getattr(beautsoup, x).extract()
        return html2text.html2text(str(beautsoup))

    def __init__(self, json_object, **kwargs):
        if json_object:
            self.from_json(self, kwargs["data"])    
        else:
            self.url = kwargs["url"]
            self.desc = kwargs["desc"]
            self.tags = kwargs["tags"].split()

            if "date" in kwargs:
                self.date = kwargs['date']
            else:
                self.date = datetime.datetime.now()
            if validators.url(self.url):
                try:
                    url_request = requests.get(self.url).text
                    parsed_html = BeautifulSoup(url_request)
                    self.content = self.extract_content(parsed_html)
                    self.title = parsed_html.title.string
                except Exception as e:
                    print(e)
                    self.wipe()
            else:
                self.wipe()

    def validate(self):
        validURL = isinstance(self.url, str) and validators.url(self.url)
        validTitle = isinstance(self.title, str)
        validContent = isinstance(self.content, str)
        validDesc = isinstance(self.desc, str)
        return validURL and validTitle and validContent and validDesc

    def insert(self):
        if self.validate():
            data = {"type": "bookmark", 'url': self.url, 'desc': self.desc, 'content': self.content, 'title': self.title, 'date': self.date.strftime("%x"), 'tags': self.tags}
            self.id = db.insert(data)
            add_to_index("dataObj", self)
            
            return self.id
        return False
