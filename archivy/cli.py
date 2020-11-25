import os
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins
from flask.cli import FlaskGroup, load_dotenv, routes_command, shell_command

from archivy import app
from archivy.check_changes import Watcher
from archivy.models import User
from archivy.click_web import create_click_web_app


def create_app():
    return app


@with_plugins(iter_entry_points('archivy.plugins'))
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass


# add built in commands:
cli.add_command(routes_command)
cli.add_command(shell_command)


@cli.command("run", short_help="Runs archivy web application")
def run():
    click.echo('Running archivy...')
    load_dotenv()
    watcher = Watcher(app)
    watcher.start()
    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    os.environ["FLASK_RUN_FROM_CLI"] = "false"
    app_with_cli = create_click_web_app(click, cli, app)
    app_with_cli.run(host='0.0.0.0', port=port)
    click.echo("Stopping archivy watcher")
    watcher.stop()
    watcher.join()


@cli.command(short_help="Creates a new admin user")
@click.argument("username")
@click.password_option()
def create_admin(username, password):
    if len(password) < 8:
        click.echo("Password length too short")
    else:
        user = User(username=username, password=password, is_admin=True)
        if user.insert():
            click.echo(f"User {username} successfully created.")
        else:
            click.echo("User with given username already exists.")
