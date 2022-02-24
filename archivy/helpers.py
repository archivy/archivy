from pathlib import Path
import sys
import os

import elasticsearch
import yaml
from elasticsearch import Elasticsearch
from flask import current_app, g, request
from tinydb import TinyDB, Query, operations
from urllib.parse import urlparse, urljoin

from archivy.config import BaseHooks, Config


def load_config(path=""):
    """Loads `config.yml` file safely and deserializes it to a python dict."""
    path = path or current_app.config["INTERNAL_DIR"]
    with (Path(path) / "config.yml").open() as f:
        return yaml.load(f.read(), Loader=yaml.SafeLoader)


def config_diff(curr_key, curr_val, parent_dict, defaults):
    """
    This function diffs the user config with the defaults to only save what is actually different.

    Returns 1 if the current element or its nested elements are different and have been preserved.
    """
    if type(curr_val) is dict:
        # the any call here diffs all nested children of the current dict and returns whether any have modifications
        if not any(
            [
                config_diff(k, v, curr_val, defaults[curr_key])
                for k, v in list(curr_val.items())
            ]
        ):
            parent_dict.pop(curr_key)
            return 0
    else:
        if defaults[curr_key] == curr_val:
            parent_dict.pop(curr_key)
            return 0
    return 1


def write_config(config: dict):
    """
    Writes a new config dict to a `config.yml` file that will override defaults.
    Compares user config with defaults to only save changes.
    """
    defaults = vars(Config())
    for k, v in list(config.items()):
        if k != "SECRET_KEY":
            config_diff(k, v, config, defaults)
    with (Path(current_app.config["INTERNAL_DIR"]) / "config.yml").open("w") as f:
        yaml.dump(config, f)


def load_hooks():
    try:
        user_hooks = (Path(current_app.config["USER_DIR"]) / "hooks.py").open()
    except FileNotFoundError:
        return BaseHooks()

    user_locals = {}
    exec(user_hooks.read(), globals(), user_locals)
    user_hooks.close()
    return user_locals.get("Hooks", BaseHooks)()


def load_scraper():
    try:
        user_scraping = (Path(current_app.config["USER_DIR"]) / "scraping.py").open()
    except FileNotFoundError:
        return {}
    user_locals = {}
    exec(user_scraping.read(), globals(), user_locals)
    user_scraping.close()
    return user_locals.get("PATTERNS", {})


def get_db(force_reconnect=False):
    """
    Returns the database object that you can use to
    store data persistently
    """
    if "db" not in g or force_reconnect:
        g.db = TinyDB(str(Path(current_app.config["INTERNAL_DIR"]) / "db.json"))

    return g.db


def get_max_id():
    """Returns the current maximum id of dataobjs in the database."""
    db = get_db()
    max_id = db.search(Query().name == "max_id")
    if not max_id:
        db.insert({"name": "max_id", "val": 0})
        return 0
    return max_id[0]["val"]


def set_max_id(val):
    """Sets a new max_id"""
    db = get_db()
    db.update(operations.set("val", val), Query().name == "max_id")


def test_es_connection(es):
    """Tests health and presence of connection to elasticsearch."""
    try:
        health = es.cluster.health()
    except elasticsearch.exceptions.ConnectionError:
        current_app.logger.error(
            "Elasticsearch does not seem to be running on "
            f"{current_app.config['SEARCH_CONF']['url']}. Please start "
            "it, for example with: sudo service elasticsearch restart"
        )
        current_app.logger.error(
            "You can disable Elasticsearch by modifying the `enabled` variable "
            f"in {str(Path(current_app.config['INTERNAL_DIR']) / 'config.yml')}"
        )
        sys.exit(1)

    if health["status"] not in ("yellow", "green"):
        current_app.logger.warning(
            "Elasticsearch reports that it is not working "
            "properly. Search might not work. You can disable "
            "Elasticsearch by setting ELASTICSEARCH_ENABLED to 0."
        )


def get_elastic_client(error_if_invalid=True):
    """Returns the elasticsearch client you can use to search and insert / delete data"""
    if (
        not current_app.config["SEARCH_CONF"]["enabled"]
        or current_app.config["SEARCH_CONF"]["engine"] != "elasticsearch"
    ) and error_if_invalid:
        return None

    auth_setup = (
        current_app.config["SEARCH_CONF"]["es_user"]
        and current_app.config["SEARCH_CONF"]["es_password"]
    )
    if auth_setup:
        es = Elasticsearch(
            current_app.config["SEARCH_CONF"]["url"],
            http_auth=(
                current_app.config["SEARCH_CONF"]["es_user"],
                current_app.config["SEARCH_CONF"]["es_password"],
            ),
        )
    else:
        es = Elasticsearch(current_app.config["SEARCH_CONF"]["url"])
    if error_if_invalid:
        test_es_connection(es)
    else:
        try:
            es.cluster.health()
        except elasticsearch.exceptions.ConnectionError:
            return False
    return es


def create_plugin_dir(name):
    """Creates a sample plugin directory"""
    raw_name = name.replace("archivy_", "").replace("archivy-", "")
    try:
        os.makedirs(f"{name}/{name}")

        # Creates requirements.txt.
        with open(f"{name}/requirements.txt", "w") as fp:
            fp.writelines(["archivy", "\nclick"])

        # Creates an empty readme file to be filled
        with open(f"{name}/README.md", "w+") as fp:
            fp.writelines(
                [
                    f"# {name}",
                    "\n\n## Install",
                    "\n\nYou need to have `archivy` already installed.",
                    f"\n\nRun `pip install archivy_{name}`",
                    "\n\n## Usage",
                ]
            )

        # Creates a setup.py file
        with open(f"{name}/setup.py", "w") as setup_f:
            setup_f.writelines(
                [
                    "from setuptools import setup, find_packages",
                    '\n\nwith open("README.md", "r") as fh:',
                    "\n\tlong_description = fh.read()",
                    '\n\nwith open("requirements.txt", encoding="utf-8") as f:',
                    '\n\tall_reqs = f.read().split("\\n")',
                    "\n\tinstall_requires = [x.strip() for x in all_reqs]",
                    "\n\n#Fill in the details below for distribution purposes"
                    f'\nsetup(\n\tname="{name}",',
                    '\n\tversion="0.0.1",',
                    '\n\tauthor="",',
                    '\n\tauthor_email="",',
                    '\n\tdescription="",',
                    "\n\tlong_description=long_description,",
                    '\n\tlong_description_content_type="text/markdown",',
                    '\n\tclassifiers=["Programming Language :: Python :: 3"],'
                    "\n\tpackages=find_packages(),",
                    "\n\tinstall_requires=install_requires,",
                    f'\n\tentry_points="""\n\t\t[archivy.plugins]'
                    f'\n\t\t{raw_name}={name}:{raw_name}"""\n)',
                ]
            )

        # Creating a basic __init__.py file where the main function of the plugin goes
        with open(f"{name}/{name}/__init__.py", "w") as fp:
            fp.writelines(
                [
                    "import archivy",
                    "\nimport click",
                    "\n\n# Fill in the functionality for the commands (see https://archivy.github.io/plugins/)",
                    "\n@click.group()",
                    f"\ndef {raw_name}():",
                    "\n\tpass",
                    f"\n\n@{raw_name}.command()",
                    "\ndef command1():",
                    "\n\tpass",
                    f"\n\n@{raw_name}.command()",
                    "\ndef command2():",
                    "\n\tpass",
                ]
            )

        return True
    except FileExistsError:
        return False


def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )
