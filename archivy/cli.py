import os
from pkg_resources import iter_entry_points

import click
import pypandoc
from click_plugins import with_plugins
from flask.cli import FlaskGroup, load_dotenv, routes_command, shell_command

from archivy import app
from archivy.check_changes import Watcher
from archivy.config import Config
from archivy.helpers import load_config, write_config
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

@cli.command("init", short_help="Initialise your archivy application")
@click.pass_context
def init(ctx):
    conf = {}
    click.echo("This is the archivy installation initialization wizard.")
    set_curr_dir = click.confirm("Use current directory as data directory for archivy?")
    if set_curr_dir:
        data_dir = os.getcwd()
    else:
        data_dir = click.prompt("Otherwise, enter the full path of the directory used to store data.", type=str)
    app.config["APP_PATH"] = data_dir
    try:
        conf = load_config()
        reset_conf = click.confirm("Config already found. Do you wish to reset it? Otherwise run archivy config")
        if reset_conf:
            conf = {}
        else:
            return
    except IOError:
        pass

    conf["data_dir"] = data_dir

    click.echo("Please enter credentials for a new admin user:")
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    if not ctx.invoke(create_admin, username=username, password=password):
        return
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        download_pandoc = click.confirm("Archivy requires Pandoc to be installed. "
                                       "Do you want us to install it automatically?")
        if download_pandoc:
            pypandoc.download_pandoc()
    # default settings
    conf["pandoc_theme"] = "pygments"
    conf["elasticsearch"] = {"enabled": 0, "url": "http://localhost:9200", "index_name": "dataobj"}

    write_config(conf)
    click.echo(f"Config successfully created at {os.path.join(app.config['APP_PATH'], 'config.yml')}")
    

@cli.command("init", short_help="Initialise your archivy application")
@click.pass_context
def init(ctx):
    try:
        load_config()
        click.confirm("Config already found. Do you wish to reset it? "
                      "Otherwise run archivy config", abort=True)
    except IOError:
        pass

    config = Config()
    delattr(config, "SECRET_KEY")

    click.echo("This is the archivy installation initialization wizard.")
    set_curr_dir = click.confirm("Use current directory as data directory for archivy?")
    if set_curr_dir:
        data_dir = os.getcwd()
    else:
        data_dir = click.prompt("Otherwise, enter the full path of the "
                                "directory where you'd like us to store data.", type=str)

    es_enabled = click.confirm("Would you like to enable Elasticsearch? For this to work "
                               "when you run archivy, you must have ES installed.")
    if es_enabled:
        config.ELASTICSEARCH_CONF["enabled"] = 1
    else:
        delattr(config, "ELASTICSEARCH_CONF")

    click.echo("Please enter credentials for a new admin user:")
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    if not ctx.invoke(create_admin, username=username, password=password):
        return

    try:
        pypandoc.get_pandoc_version()
    except OSError:
        download_pandoc = click.confirm("Archivy requires Pandoc to be installed. "
                                        "Do you want us to install it automatically?")
        if download_pandoc:
            pypandoc.download_pandoc()

    config.override({"USER_DIR": data_dir})

    write_config(vars(config))
    click.echo("Config successfully created at "
               + os.path.join(app.config['INTERNAL_DIR'], 'config.yml'))


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
        return False
    else:
        user = User(username=username, password=password, is_admin=True)
        if user.insert():
            click.echo(f"User {username} successfully created.")
            return True
        else:
            click.echo("User with given username already exists.")
            return False
