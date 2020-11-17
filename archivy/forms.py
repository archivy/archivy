from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, URL


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


class DeleteDataForm(FlaskForm):
    submit = SubmitField("Delete")


class UserForm(FlaskForm):
    username = StringField("username")
    password = PasswordField("password")
    submit = SubmitField("Submit")
