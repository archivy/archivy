from main import ELASTIC_SEARCH

def add_to_index(index, model):
    if not ELASTIC_SEARCH:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    print(payload)
    print(ELASTIC_SEARCH.index(index=index, id=model.id, body=payload))


def remove_from_index(index, id):
    if not ELASTIC_SEARCH:
        return
    ELASTIC_SEARCH.delete(index=index, id=id)

def query_index(index, query):
    if not ELASTIC_SEARCH:
        return []
    search = ELASTIC_SEARCH.search(
        index=index,
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}}})
    return search['hits']['hits']
