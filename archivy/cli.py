import os
from pkg_resources import iter_entry_points
from threading import Thread

import click
from click_plugins import with_plugins
from flask.cli import FlaskGroup, load_dotenv, routes_command, shell_command

from archivy import app
from archivy.check_changes import Watcher

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
    app.run(host='0.0.0.0', port=port)
    click.echo("Stopping archivy watcher")
    watcher.stop()
    watcher.join()


# @cli.command()
# def setup():
    # click.echo("Setting up archivy...")
