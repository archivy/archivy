from main import ELASTIC_SEARCH, app


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
