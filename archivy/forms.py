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


class MoveItemForm(FlaskForm):
    path = SelectField("Move to")
    submit = SubmitField("✓")


class RenameDirectoryForm(FlaskForm):
    new_name = StringField("New name", validators=[DataRequired()])
    current_path = HiddenField()
    submit = SubmitField("Rename current folder")


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


def config_form(current_conf, sub=0, allowed=vars(Config())):
    """
    This function defines a Config form that loads default configuration values and creates inputs for each field option

    - current_conf: object of current configuration that we will use to set the defaults
    - sub: this function is recursive and can return a sub form to represent the nesting of the config.
        Sub is a boolean value indicating whether the current form is nested.

    - allowed represents a dictionary of the keys that are allowed in our current level of nesting.
        It's fetched from the default config.
    """

    class ConfigForm(FlaskForm):
        pass

    def process_conf_value(name, val):
        """
        Create and set different form fields.

        """
        val_type = type(val)
        if not name in allowed:
            return
        if val_type is dict:
            sub_form = config_form(val, 1, allowed[name])
            setattr(ConfigForm, name, FormField(sub_form))
        elif val_type is int:
            setattr(ConfigForm, name, IntegerField(name, default=val))
        elif val_type is str:
            setattr(ConfigForm, name, StringField(name, default=val))
        elif val_type is bool:
            setattr(ConfigForm, name, BooleanField(name, default=val))
        elif val_type is list:
            setattr(ConfigForm, name, StringField(name, default=", ".join(val)))

    for key, val in current_conf.items():
        process_conf_value(key, val)
    if sub:
        return ConfigForm
    else:
        ConfigForm.submit = SubmitField("Submit")
        return ConfigForm()
