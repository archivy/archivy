from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, HiddenField
from wtforms.validators import DataRequired, URL


class NewBookmarkForm(FlaskForm):
    url = StringField("url", validators=[DataRequired(), URL()])
    tags = StringField("tags")
    path = SelectField("Folder")
    submit = SubmitField("Save")


class NewNoteForm(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    tags = StringField("tags")
    path = SelectField("Folder")
    submit = SubmitField("Save")


class NewFolderForm(FlaskForm):
    parent_dir = HiddenField()
    new_dir = StringField("New folder", validators=[DataRequired()])
    submit = SubmitField("Create sub directory")


class DeleteDataForm(FlaskForm):
    submit = SubmitField("Delete")


class DeleteFolderForm(FlaskForm):
    dir_name = HiddenField(validators=[DataRequired()])


class UserForm(FlaskForm):
    username = StringField("username")
    password = PasswordField("password")
    submit = SubmitField("Submit")
