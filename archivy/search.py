from pypandoc import convert_text

from archivy.extensions import get_elastic_client


def add_to_index(index, model):
    es = get_elastic_client()
    if not es:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    es.index(index=index, id=model.id, body=payload)


def remove_from_index(index, dataobj_id):
    es = get_elastic_client()
    if not es:
        return
    es.delete(index=index, id=dataobj_id)


def query_index(index, query):
    es = get_elastic_client()
    if not es:
        return []
    search = es.search(
        index=index,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"],
                    "analyzer": "rebuilt_standard"
                }
            },
            "highlight" : {
                "fields" : {
                    "content" : {
                        "pre_tags": "<span style='background-color: #f6efa6'>",
                        "post_tags": "</span>",
                        "boundary_max_scan": 200,
                        "fragment_size": 0
                    }
                }
            }
        }           
    )

    hits = []
    for hit in search["hits"]["hits"]:
        formatted_hit = {"id": hit["_id"], "title": hit["_source"]["title"], "highlight": []}

        if "highlight" in hit:
            for highlight in hit["highlight"]["content"]:
                formatted_hit["highlight"].append(convert_text(highlight, "html", format="md"))

        hits.append(formatted_hit)

    return hits
