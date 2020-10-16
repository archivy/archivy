import os
import appdirs


class Config(object):
    ELASTICSEARCH_ENABLED = int(os.environ.get("ELASTICSEARCH_ENABLED") or 0)
    ELASTICSEARCH_URL = os.environ.get(
        "ELASTICSEARCH_URL") or "http://localhost:9200"
    SECRET_KEY = os.urandom(32)
    INDEX_NAME = "dataobj"
    APP_PATH = \
        os.getenv('ARCHIVY_DATA_DIR') or appdirs.user_data_dir('archivy')
    os.makedirs(APP_PATH, exist_ok=True)

    PANDOC_HIGHLIGHT_THEME = os.environ.get("PANDOC_THEME") or "pygments"
    ELASTIC_CONF = {
        "settings": {
            "highlight": {
                "max_analyzed_offset": 100000000
            },
            "analysis": {
                "analyzer": {
                    "rebuilt_standard": {
                        "stopwords": "_english_",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "kstem",
                            "trim",
                            "unique"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "rebuilt_standard",
                    "term_vector": "with_positions_offsets"
                },
                "tags": {"type": "text", "analyzer": "rebuilt_standard"},
                "body": {"type": "text", "analyzer": "rebuilt_standard"},
                "desc": {"type": "text", "analyzer": "rebuilt_standard"}
            }
        }
    }
