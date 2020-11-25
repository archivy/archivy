import os
import sys

import elasticsearch
from elasticsearch import Elasticsearch
from flask import current_app, g
from tinydb import TinyDB, Query, operations

from archivy.config import Config


def get_db(force_reconnect=False):
    """
    Returns the database object that you can use to
    store data persistently
    """
    if 'db' not in g or force_reconnect:
        g.db = TinyDB(
            os.path.join(
                current_app.config['APP_PATH'],
                'db.json'
            )
        )

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
    if not current_app.config['ELASTICSEARCH_ENABLED']:
        return None

    es = Elasticsearch(current_app.config['ELASTICSEARCH_URL'])
    try:
        health = es.cluster.health()
    except elasticsearch.exceptions.ConnectionError:
        current_app.logger.error(
            "Elasticsearch does not seem to be running on "
            f"{Config.ELASTICSEARCH_URL}. Please start "
            "it, for example with: sudo service elasticsearch restart"
        )
        current_app.logger.error(
            "You can disable Elasticsearch by setting the "
            "ELASTICSEARCH_ENABLED environment variable to 0"
        )
        sys.exit(1)

    if health["status"] not in ("yellow", "green"):
        current_app.logger.warning(
            "Elasticsearch reports that it is not working "
            "properly. Search might not work. You can disable "
            "Elasticsearch by setting ELASTICSEARCH_ENABLED to 0."
        )
    return es
