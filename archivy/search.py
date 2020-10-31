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
            "highlight": {
                "fields": {
                    "content": {
                        "pre_tags": "<span class='matches'>",
                        "post_tags": "</span>",
                        "boundary_max_scan": 200,
                        "fragment_size": 0
                    }
                }
            }
        }
    )

    text = ""
    for hit in search["hits"]["hits"]:
        text += f"<li>[{hit['_source']['title']}](/dataobj/{hit['_id']})<br><br>    "
        if "highlight" in hit:
            for highlight in hit["highlight"]["content"]:
                text += f"{highlight}"
        text += "</li>"

    return convert_text(text, "html", format="md")
