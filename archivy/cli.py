import os
from pkg_resources import iter_entry_points
from threading import Thread

import click
from click_plugins import with_plugins
from flask.cli import FlaskGroup, load_dotenv, with_appcontext

from archivy import app
from archivy.check_changes import run_watcher


def create_app():
    return app

@with_plugins(iter_entry_points('archivy.plugins'))
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass


@cli.command()
def run():
    click.echo('Running archivy...')
    load_dotenv()
    # prevent pytest from hanging because of running thread
    Thread(target=run_watcher, args=[app]).start()
    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    os.environ["FLASK_RUN_FROM_CLI"] = "false"
    app.run(host='0.0.0.0', port=port)


@cli.command()
def setup():
    click.echo("Setting up archivy...")
