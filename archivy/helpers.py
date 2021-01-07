from pathlib import Path
import sys

import elasticsearch
import yaml
from elasticsearch import Elasticsearch
from flask import current_app, g
from tinydb import TinyDB, Query, operations

from archivy.config import BaseHooks


def load_config(path=""):
    """Loads `config.yml` file safely and deserializes it to a python dict."""
    path = path or current_app.config["INTERNAL_DIR"]
    with (Path(path) / "config.yml").open() as f:
        return yaml.load(f.read(), Loader=yaml.SafeLoader)


def write_config(config: dict):
    """Writes a new config dict to a `config.yml` file that will override defaults"""
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

    return user_locals["Hooks"]()


def get_db(force_reconnect=False):
    """
    Returns the database object that you can use to
    store data persistently
    """
    if 'db' not in g or force_reconnect:
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


def get_elastic_client():
    """Returns the elasticsearch client you can use to search and insert / delete data"""
    if not current_app.config["SEARCH_CONF"]["enabled"]:
        return None

    es = Elasticsearch(current_app.config["SEARCH_CONF"]["url"])
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
    return es
