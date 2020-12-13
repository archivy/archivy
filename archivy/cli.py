import os
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins
from flask.cli import FlaskGroup, load_dotenv, shell_command

from archivy import app
from archivy.check_changes import Watcher
from archivy.config import Config
from archivy.click_web import create_click_web_app
from archivy.data import open_file, reformat_file
from archivy.helpers import load_config, write_config
from archivy.models import User


def create_app():
    return app


@with_plugins(iter_entry_points('archivy.plugins'))
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass


# add built in commands:
cli.add_command(shell_command)


@cli.command("init", short_help="Initialise your archivy application")
@click.pass_context
def init(ctx):
    try:
        load_config()
        click.confirm("Config already found. Do you wish to reset it? "
                      "Otherwise run `archivy config`", abort=True)
    except FileNotFoundError:
        pass

    config = Config()
    delattr(config, "SECRET_KEY")

    click.echo("This is the archivy installation initialization wizard.")
    data_dir = click.prompt("Enter the full path of the "
                            "directory where you'd like us to store data.",
                            type=str,
                            default=os.getcwd())

    es_enabled = click.confirm("Would you like to enable Elasticsearch? For this to work "
                               "when you run archivy, you must have ES installed."
                               "See https://archivy.github.io/setup-search/ for more info.")
    if es_enabled:
        config.SEARCH_CONF["enabled"] = 1
    else:
        delattr(config, "SEARCH_CONF")

    create_new_user = click.confirm("Would you like to create a new admin user?")
    if create_new_user:
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        if not ctx.invoke(create_admin, username=username, password=password):
            return

    config.HOST = click.prompt("Host [localhost (127.0.0.1)]",
                               type=str, default="127.0.0.1", show_default=False)

    config.override({"USER_DIR": data_dir})
    app.config["USER_DIR"] = data_dir

    # create data dir
    os.makedirs(os.path.join(data_dir, "data"), exist_ok=True)

    write_config(vars(config))
    click.echo("Config successfully created at "
               + os.path.join(app.config['INTERNAL_DIR'], 'config.yml'))


@cli.command("config", short_help="Open archivy config.")
def config():
    open_file(os.path.join(app.config["INTERNAL_DIR"], "config.yml"))


@cli.command("run", short_help="Runs archivy web application")
def run():
    click.echo('Running archivy...')
    load_dotenv()
    if app.config["SEARCH_CONF"]["enable_watcher"]:
        watcher = Watcher(app)
        watcher.start()
    os.environ["FLASK_RUN_FROM_CLI"] = "false"
    app_with_cli = create_click_web_app(click, cli, app)
    app_with_cli.run(host=app.config["HOST"], port=app.config["PORT"])
    click.echo("Stopping archivy watcher")
    if app.config["SEARCH_CONF"]["enable_watcher"]:
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


@cli.command(short_help="Format normal markdown files for archivy.")
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def format(filenames):
    for path in filenames:
        reformat_file(path)
