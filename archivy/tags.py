import re

from flask import current_app
from archivy import helpers, data
from tinydb import Query, operations
from archivy.search import query_ripgrep_tags


def is_tag_format(tag_name):
    return re.match("^[a-zA-Z0-9_-]+$", tag_name)


def get_all_tags(force=False):
    db = helpers.get_db()
    list_query = db.search(Query().name == "tag_list")

    # If the "tag_list" doesn't exist in the database: create it.
    newly_created = list_query == []
    if newly_created:
        db.insert({"name": "tag_list", "val": []})

    # Then update it if needed
    tags = []
    if newly_created or force:
        tags = list(query_ripgrep_tags())
        db.update(operations.set("val", tags), Query().name == "tag_list")
    else:
        tags = list_query[0]["val"]
    return tags


def add_tag_to_index(tag_name):
    all_tags = get_all_tags()
    if tag_name not in all_tags:
        all_tags.append(tag_name)
        db = helpers.get_db()
        db.update(operations.set("val", all_tags), Query().name == "tag_list")
    return True
