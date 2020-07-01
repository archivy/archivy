from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL, ValidationError
from tinydb import TinyDB, Query
from app import db
import re

class NewBookmarkForm(FlaskForm):
    url = StringField('url', validators=[DataRequired(), URL()])
    desc = StringField('desc')
    tags = StringField('tags')
    submit = SubmitField('Save')

    def validate_url(self, url):
        Bookmark = Query()
        if len(db.search(Bookmark.type == "bookmark" and Bookmark.url == url.data)) > 0:
            raise ValidationError("You have already saved this bookmark.")
        
class PocketForm(FlaskForm):
    api_key = StringField('Pocket API key')
    submit = SubmitField('Save')

    def validate_api_key(self, api_key):
        key_regex = "\d{5}-\w{24}"
        if not re.match(key_regex, api_key.data):
            raise ValidationError("Invalid API key.")

class DeleteDataForm(FlaskForm):
    submit = SubmitField("Delete")
