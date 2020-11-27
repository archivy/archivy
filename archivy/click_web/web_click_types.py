"""
Extra click types that could be useful in a web context as
they have corresponding HTML form input type.
The custom web click types need only be imported
into the main script, not the app.py that flask runs.

Example usage in your click command:
\b
    from click_web.web_click_types import EMAIL_TYPE
    @cli.command()
    @click.option("--the_email", type=EMAIL_TYPE)
    def email(the_email):
        click.echo(f"{the_email} is a valid email syntax.")

"""
import re

import click


class EmailParamType(click.ParamType):
    name = 'email'
    EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    def convert(self, value, param, ctx):
        if self.EMAIL_REGEX.match(value):
            return value
        else:
            self.fail(f'{value} is not a valid email', param, ctx)


class PasswordParamType(click.ParamType):
    name = "password"

    def convert(self, value, param, ctx):
        return value


EMAIL_TYPE = EmailParamType()
PASSWORD_TYPE = PasswordParamType()
