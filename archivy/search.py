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
                    "analyzer": "rebuilt_standard"}}},
    )

    return search["hits"]["hits"]
