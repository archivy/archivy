import os
from threading import Thread

import click
from flask.cli import FlaskGroup, load_dotenv

from archivy import app
from archivy.check_changes import Watcher


def create_app():
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass


@cli.command()
def run():
    click.echo('Running archivy...')
    load_dotenv()
    # prevent pytest from hanging because of running thread
    watcher = Watcher(app)
    watcher.start()
    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    os.environ["FLASK_RUN_FROM_CLI"] = "false"
    app.run(host='0.0.0.0', port=port)
    # this code will be reached when the user stops running the server by doing CTRL+C
    watcher.stop()
    watcher.join()


@cli.command()
def setup():
    click.echo("Setting up archivy...")
