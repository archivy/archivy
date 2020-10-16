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

    hits = []
    for hit in search["hits"]["hits"]:
        formatted_hit = {"id": hit["_id"], "title": hit["_source"]["title"], "highlight": []}
        if "highlight" in hit:
            # FIXME: find a way to make this less hacky and
            # yet still conserve logical separations
            # hack to make pandoc faster by converting highlights in one go
            # join highlights into string with symbolic separator
            SEPARATOR = "SEPARATOR.m.m.m.m.m.m.m.m.m.SEPARATOR"
            concatenated_highlight = SEPARATOR.join(
                    [highlight for highlight in hit["highlight"]["content"]])
            # re split highlights
            formatted_hit["highlight"] = convert_text(concatenated_highlight,
                                                      "html",
                                                      format="md").split(SEPARATOR)

        hits.append(formatted_hit)

    return hits
