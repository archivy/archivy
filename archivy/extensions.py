from tinydb import TinyDB, Query, operations
from elasticsearch import Elasticsearch
from archivy.config import Config


DB = TinyDB(Config.APP_PATH + "/db.json")


def get_max_id():
    max_id = DB.search(Query().name == "max_id")
    if not max_id:
        DB.insert({"name": "max_id", "val": 0})
        return 0
    return max_id[0]["val"]


def set_max_id(val):
    DB.update(operations.set("val", val), Query().name == "max_id")


def elastic_client():
    return Elasticsearch([Config.ELASTICSEARCH_URL]
                         ) if Config.ELASTICSEARCH_ENABLED else None
