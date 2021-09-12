from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
    PasswordField,
    HiddenField,
    BooleanField,
    FormField,
)
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, URL
from archivy.config import Config


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


class MoveDataForm(FlaskForm):
    path = SelectField("Move to")
    submit = SubmitField("✓")


class DeleteDataForm(FlaskForm):
    submit = SubmitField("Delete")


class DeleteFolderForm(FlaskForm):
    dir_name = HiddenField(validators=[DataRequired()])


class UserForm(FlaskForm):
    username = StringField("username")
    password = PasswordField("password")
    submit = SubmitField("Submit")


class TitleForm(FlaskForm):
    title = StringField("title")
    submit = SubmitField("✓")


def config_form(example_conf, ignore=[], sub=0):
    class ConfigForm(FlaskForm):
        pass

    def process_conf_value(name, val, allowed):
        val_type = type(val)
        if not name in allowed and not sub:
            return
        if val_type is dict:
            sub_form = config_form(val, ignore, 1)
            setattr(ConfigForm, name, FormField(sub_form))
        elif val_type is int:
            setattr(ConfigForm, name, IntegerField(name, default=val))
        elif val_type is str:
            setattr(ConfigForm, name, StringField(name, default=val))
        elif val_type is bool:
            setattr(ConfigForm, name, BooleanField(name, default=val))
        elif val_type is list:
            setattr(ConfigForm, name, StringField(name, default=", ".join(val)))

    for key, val in example_conf.items():
        if not key in ignore:
            process_conf_value(key, val, vars(Config()))
    if sub:
        return ConfigForm
    else:
        ConfigForm.submit = SubmitField("Submit")
        return ConfigForm()
