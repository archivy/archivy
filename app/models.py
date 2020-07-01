import validators
from app import db
import requests
import html2text
from bs4 import BeautifulSoup
import re
import datetime
from app.search import *
from urllib.parse import urljoin

class DataObj:
    __searchable__ = ['title', 'content', 'desc', 'tags']

    def process_bookmark_url(self):
        try:
            url_request = requests.get(self.url).text
            parsed_html = BeautifulSoup(url_request)
            self.content = self.extract_content(parsed_html)
            self.title = parsed_html.title.string
        except Exception as e:
            print(e)
            self.wipe()

    def wipe(self):
        self.title = None
        self.desc = None
        self.content = None

    def extract_content(self, beautsoup):
        stripped_tags = ['footer', 'nav']
        url = self.url.rstrip("/")

        for x in stripped_tags:
            if getattr(beautsoup, x):
                getattr(beautsoup, x).extract()
        resources = beautsoup.find_all(['a', 'img'])
        for external in resources:
            if external.name == 'a' and external['href'].startswith('/'):
                external['href'] = urljoin(url, external['href'])
            elif external.name == 'img' and external['src'].startswith('/'):
                external['src'] = urljoin(url, external['src'])

        return html2text.html2text(str(beautsoup))

    def __init__(self, **kwargs):
        self.desc = kwargs["desc"]
        self.tags = kwargs["tags"].split()
        self.type = kwargs["type"]
        if "date" in kwargs:
            self.date = kwargs['date']
        else:
            self.date = datetime.datetime.now()
        if self.type == "bookmark":
            self.url = kwargs["url"]
            if validators.url(self.url):
                self.process_bookmark_url()
            
    def validate(self):
        validURL = isinstance(self.url, str) and validators.url(self.url)
        validTitle = isinstance(self.title, str)
        validContent = isinstance(self.content, str)
        validDesc = isinstance(self.desc, str)
        return validURL and validTitle and validContent and validDesc

    def insert(self):
        if self.validate():
            data = {"type": self.type, 'url': self.url, 'desc': self.desc, 'content': self.content, 'title': self.title, 'date': self.date.strftime("%x"), 'tags': self.tags}
            self.id = db.insert(data)
            if self.id:
                add_to_index("dataobj", self)
            
            return self.id
        return False
