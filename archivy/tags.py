from flask import current_app
from archivy import helpers, data
from tinydb import Query, operations
from archivy.search import query_ripgrep_tags


def get_all_tags(force=False):
    db = helpers.get_db()
    list_query = db.search(Query().name == "list_of_tags")

    # If the "list_of_tags" doesn't exist in the database: create it.
    newly_created = list_query == []
    if newly_created:
        db.insert({"name": "list_of_tags", "val": []})

    # Then update it if needed
    if newly_created or force:
        tags = query_ripgrep_tags()
        db.update(operations.set("val", list(tags)), Query().name == "list_of_tags")
    else:
        tags = list_query[0]["val"]

    return tags


def add_tag_to_index(tag_name):
    all_tags = get_all_tags()
    if tag_name not in all_tags:
        all_tags.append(tag_name)
        db = helpers.get_db()
        db.update(operations.set("val", all_tags), Query().name == "list_of_tags")
    return True
