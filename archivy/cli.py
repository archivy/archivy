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

import os

import click
from flask.cli import FlaskGroup, load_dotenv, routes_command, shell_command

from archivy import app
from archivy.check_changes import Watcher


def show_license(ctx, param, value):  # noqa:
    """Prints the license of the utility"""
    if not value or ctx.resilient_parsing:
        return
    click.echo(__doc__)
    ctx.exit()


def create_app():
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
@click.option('--license', '--lic', is_flag=True,
              callback=show_license,
              expose_value=False, is_eager=True)
def cli():
    pass


# add built in commands:
cli.add_command(routes_command)
cli.add_command(shell_command)


@cli.command("run", short_help="Runs archivy web application")
def run():
    click.echo('Running archivy...')
    load_dotenv()
    # prevent pytest from hanging because of running thread
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
