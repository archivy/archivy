import re
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, URL, ValidationError


class NewBookmarkForm(FlaskForm):
    url = StringField("url", validators=[DataRequired(), URL()])
    path = SelectField("Topic")
    desc = StringField("desc")
    tags = StringField("tags")
    submit = SubmitField("Save")


class NewNoteForm(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    path = SelectField("Topic")
    desc = StringField("desc")
    tags = StringField("tags")
    submit = SubmitField("Save")


class PocketForm(FlaskForm):
    api_key = StringField("Pocket API key")
    submit = SubmitField("Save")

    def validate_api_key(self, api_key):
        key_regex = r"\d{5}-\w{24}"
        if not re.match(key_regex, api_key.data):
            raise ValidationError("Invalid API key.")


class DeleteDataForm(FlaskForm):
    submit = SubmitField("Delete")


class UserForm(FlaskForm):
    username = StringField("username")
    password = PasswordField("password")
    submit = SubmitField("Submit")
