from flask import current_app
from archivy import helpers, data
from tinydb import Query

# Get all tags with counts from all_items and return a list
# all_tags = [
#     { "tag1": count },
#     { "tag2": count },
#     ...
# }
def get_all_tags_with_counts(all_items=None, force=False):
    db = helpers.get_db()
    if all_items is None:
        all_items = data.get_items(structured=False)
    list_query = db.search(Query().name == "list_of_tags")

    if not list_query or force:
        print("searching for tags")
        all_tags = {}
        for item in all_items:
            for this_tag in item.get("tags", []):
                if this_tag not in list(all_tags):
                    all_tags[this_tag] = {"count": 1}
                else:
                    all_tags[this_tag]["count"] += 1

        if not list_query:
            db.insert({"name": "list_of_tags", "val": all_tags})
        else:
            db.update(all_tags, Query().name == "list_of_tags")
    else:
        all_tags = list_query[0]["val"]

    return all_tags


def get_all_tags():
    with_counts = get_all_tags_with_counts()
    without_counts = list(with_counts)

    return without_counts


def add_tag_to_index(tagname):
    all_tags = get_all_tags_with_counts(force=True)
    if tagname in all_tags:
        print(all_tags[tagname])
        all_tags[tagname]["count"] += 1
    else:
        all_tags[tagname]["count"] = 1
    db = helpers.get_db()
    res = db.update(all_tags, Query().name == "list_of_tags")
