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
        return_tags = query_ripgrep_tags()
        db.update(
            operations.set("val", list(return_tags)), Query().name == "list_of_tags"
        )
    else:
        return_tags = list_query[0]["val"]

    return return_tags


def get_tags_for_dataobj(dataobj_id):
    all_tags = get_all_tags()
    tags = []
    for tag_name, tag_entry in all_tags.items():
        if str(dataobj_id) in tag_entry:
            tags.append(tag_name)

    return tags


def add_tag_to_index(tagname):
    all_tags = get_all_tags()
    if tagname not in all_tags:
        all_tags.append(tagname)
        print("new all_tags", all_tags)

        db = helpers.get_db()
        db.update(operations.set("val", all_tags), Query().name == "list_of_tags")

    return True
