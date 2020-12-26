from elasticsearch.exceptions import RequestError
from flask import current_app

from archivy.helpers import get_elastic_client


def add_to_index(model):
    """
    Adds dataobj to given index. If object of given id already exists, it will be updated.

    Params:

    - **index** - String of the ES Index. Archivy uses `dataobj` by default.
    - **model** - Instance of `archivy.models.Dataobj`, the object you want to index.
    """
    es = get_elastic_client()
    if not es:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    es.index(index=current_app.config["SEARCH_CONF"]["index_name"], id=model.id, body=payload)
    return True


def remove_from_index(dataobj_id):
    """Removes object of given id"""
    es = get_elastic_client()
    if not es:
        return
    es.delete(index=current_app.config["SEARCH_CONF"]["index_name"], id=dataobj_id)


def query_index(query):
    """Returns search results for your given query"""
    es = get_elastic_client()
    if not es:
        return []
    search = es.search(
        index=current_app.config["SEARCH_CONF"]["index_name"],
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"],
                    "analyzer": "rebuilt_standard"
                }
            },
            "highlight": {
                "fragment_size": 0,
                "fields": {
                    "content": {
                        "pre_tags": "==",
                        "post_tags": "==",
                    }
                }
            }
        }
    )

    hits = []
    for hit in search["hits"]["hits"]:
        formatted_hit = {"id": hit["_id"], "title": hit["_source"]["title"]}
        if "highlight" in hit:
            formatted_hit["highlight"] = hit["highlight"]["content"]
        hits.append(formatted_hit)

    return hits


def create_es_index():
    es = get_elastic_client()
    try:
        es.indices.create(
            index=current_app.config["SEARCH_CONF"]["index_name"],
            body=current_app.config["SEARCH_CONF"]["search_conf"])
    except RequestError:
        current_app.logger.info("Elasticsearch index already created")


def create_lunr_index(documents):
    """Creates and configures the Lunr index."""
    from lunr.builder import Builder
    from lunr.stemmer import stemmer
    from lunr.trimmer import trimmer
    from lunr.stop_word_filter import stop_word_filter
    builder = Builder()
    builder.pipeline.add(trimmer, stop_word_filter, stemmer)
    builder.search_pipeline.add(stemmer)
    builder.metadata_whitelist = ["position"]
    builder.ref("id")
    fields = [{"field_name": "title", "boost": 10},
              {"field_name": "body", "extractor": lambda doc: doc.content}]
    for field in fields:
        builder.field(**field)
    for document in documents:
        builder.add(document)
    return builder.build()
