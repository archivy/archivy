import validators
from app import db
import requests
from markdownify import markdownify as md

class Bookmark:
    def from_json(self, data):
        self.url = data["url"]
        self.title = data["title"]
        self.content = data["content"]
        self.desc = data["desc"]

    def __init__(self, json_object, **kwargs):
        if json_object:
            from_json(self, kwargs["data"])    
        else:
            self.url = kwargs["url"]
            self.desc = kwargs["desc"]
            url_request = requests.get(self.url)
            self.content = 


    def validate(self):
        validURL = isinstance(self.url, str) and validators.url(self.url)
        validTitle = isinstance(self.title, str)
        validContent = isinstance(self.content, str)
        validDesc = isinstance(self.desc, str)
        return validURL and validTitle and validContent and validDesc

    def insert(self):
        if self.validate():
            db.insert({"type": "bookmark", 'url': self.url, 'desc': self.desc, 'content': self.content})
            return True
        return False
    
