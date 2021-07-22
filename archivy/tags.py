from flask import current_app
from archivy import helpers, data
from tinydb import Query

# Get all tags with counts from all_items and return a list
# all_tags = [
#     { "tag1": count },
#     { "tag2": count },
#     ...
# }
def get_all_tags_with_counts(all_items=None):
    db = helpers.get_db()
    if all_items is None:
        all_items = data.get_items(structured=False)
    list_query = db.search(Query().name == "list_of_tags")

    if not list_query:
        print("searching")
        all_tags = {}
        for item in all_items:
            for this_tag in item["tags"]:
                if this_tag not in list(all_tags):
                    all_tags[this_tag] = {"count": 1}
                else:
                    all_tags[this_tag]["count"] += 1

        list_of_tags = []
        for this_tag in list(all_tags):
            list_of_tags.append(
                {"tagname": this_tag, "count": all_tags[this_tag]["count"]}
            )
        db.insert({"name": "list_of_tags", "val": list_of_tags})
    else:
        list_of_tags = list_query[0]["val"]

    return list_of_tags


def get_all_tags():
    db = helpers.get_db()
    list_query = db.search(Query().name == "list_of_tags")

    if not list_query:
        print("searching")
        all_tags = {}
        for item in all_items:
            for this_tag in item["tags"]:
                if this_tag not in list(all_tags):
                    all_tags[this_tag] = {"count": 1}
                else:
                    all_tags[this_tag]["count"] += 1

        list_of_tags = []
        for this_tag in list(all_tags):
            list_of_tags.append(
                {"tagname": this_tag, "count": all_tags[this_tag]["count"]}
            )
        db.insert({"name": "list_of_tags", "val": list_of_tags})
    else:
        list_of_tags = list_query[0]["val"]

    return list_of_tags
