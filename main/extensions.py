import os

from tinydb import TinyDB, Query, operations
from elasticsearch import Elasticsearch

ELASTIC_URL = os.environ.get("ELASTICSEARCH_URL")
DB = TinyDB("db.json")

def get_max_id():
    max_id = DB.search(Query().name == "max_id")
    if not max_id:
        DB.insert({"name": "max_id", "val": 0})
    
    else: return max_id[0]["val"]

def set_max_id(val):
    DB.update(operations.set("val", val), Query().name == "max_id")


def elastic_client():
    return Elasticsearch([ELASTIC_URL]) if os.environ.get("ELASTICSEARCH_ENABLED") else None
