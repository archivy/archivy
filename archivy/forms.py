#!/usr/bin/env python
"""
Archivy: self-hosted knowledge repository that allows you to safely preserve
useful content that contributes to your knowledge bank.

Copyright (C) 2020 The Archivy Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

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
