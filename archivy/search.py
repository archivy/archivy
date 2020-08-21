from archivy.extensions import elastic_client

ELASTICSEARCH = elastic_client()

def add_to_index(index, model):
    if not ELASTICSEARCH:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    ELASTICSEARCH.index(index=index, id=model.id, body=payload)

def remove_from_index(index, dataobj_id):
    if not ELASTICSEARCH:
        return
    ELASTICSEARCH.delete(index=index, id=dataobj_id)

def query_index(index, query):
    if not ELASTICSEARCH:
        return []
    search = ELASTICSEARCH.search(
        index=index,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"],
                    "analyzer": "rebuilt_standard"}}},
    )

    return search["hits"]["hits"]
