import os

from flask import current_app, g
from tinydb import TinyDB, Query, operations
from elasticsearch import Elasticsearch
from archivy.config import Config


def get_db():
    if 'db' not in g:
        g.db = TinyDB(
            os.path.join(
                current_app.config['APP_PATH'],
                'db.json'
            )
        )

    return g.db


def get_max_id():
    db = get_db()
    max_id = db.search(Query().name == "max_id")
    if not max_id:
        db.insert({"name": "max_id", "val": 0})
        return 0
    return max_id[0]["val"]


def set_max_id(val):
    db = get_db()
    db.update(operations.set("val", val), Query().name == "max_id")


def elastic_client():
    return Elasticsearch([Config.ELASTICSEARCH_URL]
                         ) if Config.ELASTICSEARCH_ENABLED else None
