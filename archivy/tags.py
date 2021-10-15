from flask import current_app
from archivy import helpers, data
from tinydb import Query, operations
from archivy.search import query_ripgrep_tags

# Get all tags with counts from all_items and return a list
# return_tags = {
#     "tag": {
#         dataobj_id: dataobj_title,
#         dataobj_id: dataobj_title,
#         ...
#         count: N
#     }
# }
def get_all_tags(force=False):
    rg_tags = query_ripgrep_tags()

    db = helpers.get_db()
    list_query = db.search(Query().name == "list_of_tags")

    newly_created = list_query == []
    if newly_created:
        db.insert({"name": "list_of_tags", "val": {}})

    if newly_created or force:
        return_tags = {}
        for result in rg_tags:
            pk = str(result[0])
            tag = result[1][1:]  # Getting rid of the "#"

            item = data.get_item(pk)

            if tag not in list(return_tags):
                return_tags[tag] = {pk: item["title"], "count": 1}
            else:
                if not pk in return_tags[tag]:
                    return_tags[tag]["count"] += 1
                return_tags[tag][pk] = item["title"]

        db.update(operations.set("val", return_tags), Query().name == "list_of_tags")
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


def add_tag_to_index(tagname, dataobj_id):
    all_tags = get_all_tags()
    item = data.get_item(dataobj_id)
    if tagname in all_tags.keys():
        all_tags[tagname]["count"] += 1
        all_tags[tagname][dataobj_id] = item["title"]
    else:
        all_tags[tagname] = {"count": 1, dataobj_id: item["title"]}

    db = helpers.get_db()
    db.update(operations.set("val", all_tags), Query().name == "list_of_tags")

    return True
