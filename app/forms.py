from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from tinydb import TinyDB, Query
from app import db

class NewBookmarkForm(FlaskForm):
    url = StringField('url', validators=[DataRequired(), URL()])
    desc = StringField('desc')
    submit = SubmitField('Save')

    def validate_url(self, url):
        Bookmark = Query()
        if len(db.search(Bookmark.type == "bookmark" and Bookmark.url == url)) > 0:
            raise ValidationError("You have already saved this bookmark")
        