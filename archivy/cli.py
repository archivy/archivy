import os

import click
from flask.cli import FlaskGroup, load_dotenv

from archivy import app


@click.group(cls=FlaskGroup)
def cli():
    pass


@cli.command()
def run():
    click.echo('Running archivy...')
    load_dotenv()
    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    app.run(host='0.0.0.0', port=port)


@cli.command()
def setup():
    click.echo("Setting up archivy...")
