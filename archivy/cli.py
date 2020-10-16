import os
from threading import Thread

import click
from flask.cli import FlaskGroup, load_dotenv

from archivy import app
from archivy.check_changes import run_watcher

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
    Thread(target=run_watcher, args=[app]).start()

    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    os.environ["FLASK_RUN_FROM_CLI"] = "false"
    app.run(host='0.0.0.0', port=port)


@cli.command()
def setup():
    click.echo("Setting up archivy...")
