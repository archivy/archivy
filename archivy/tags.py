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
def get_all_tags(force=False):
    rg_tags = query_ripgrep_tags()

    db = helpers.get_db()
    list_query = db.search(Query().name == "list_of_tags")

    if not list_query or force or True:
        return_tags = {}
        for result in rg_tags:
            pk = result[0]
            tag = result[1][1:]  # Getting rid of the "#"

            item = data.get_item(pk)

            if tag not in list(return_tags):
                return_tags[tag] = {item["id"]: item["title"], "count": 1}
            else:
                if not item["id"] in return_tags[tag]:
                    return_tags[tag]["count"] += 1
                return_tags[tag][item["id"]] = item["title"]

        if not list_query:
            db.insert({"name": "list_of_tags", "val": return_tags})
        else:
            db.update(
                operations.set("val", return_tags), Query().name == "list_of_tags"
            )
    else:
        return_tags = list_query[0]["val"]

    return return_tags


def add_tag_to_index(tagname):
    all_tags = get_all_tags(force=True)
    if tagname in all_tags:
        print(all_tags[tagname])
        all_tags[tagname]["count"] += 1
    else:
        all_tags[tagname]["count"] = 1
    db = helpers.get_db()
    db.update(all_tags, Query().name == "list_of_tags")
