from flask import current_app
from archivy import helpers, data
from tinydb import Query, operations
from archivy.search import query_ripgrep_tags

# Get all tags with counts from all_items and return a list
# all_tags = [
#     { "tag1": count },
#     { "tag2": count },
#     ...
# }
def get_all_tags(all_items=None, force=False):
    rg_tags = query_ripgrep_tags()
    print(rg_tags)
    return_tags = {}
    for tag in rg_tags:
        return_tags[tag] = 1

    return return_tags

    db = helpers.get_db()
    if all_items is None:
        all_items = data.get_items(structured=False)
    list_query = db.search(Query().name == "list_of_tags")

    if not list_query or force:
        all_tags = {}
        for item in all_items:
            for tag in item.get("tags", []):
                if tag not in list(all_tags):
                    all_tags[tag] = {item["id"]: item["title"], "count": 1}
                else:
                    if not item["id"] in all_tags[tag]:
                        all_tags[tag]["count"] += 1
                    all_tags[tag][item["id"]] = item["title"]

        if not list_query:
            db.insert({"name": "list_of_tags", "val": all_tags})
        else:
            db.update(operations.set("val", all_tags), Query().name == "list_of_tags")
    else:
        all_tags = list_query[0]["val"]
    return all_tags


def add_tag_to_index(tagname):
    all_tags = get_all_tags(force=True)
    if tagname in all_tags:
        print(all_tags[tagname])
        all_tags[tagname]["count"] += 1
    else:
        all_tags[tagname]["count"] = 1
    db = helpers.get_db()
    db.update(all_tags, Query().name == "list_of_tags")
