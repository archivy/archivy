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
    ELASTIC_CONF = {
        "settings": {
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
                "title": {"type": "text", "analyzer": "rebuilt_standard"},
                "tags": {"type": "text", "analyzer": "rebuilt_standard"},
                "body": {"type": "text", "analyzer": "rebuilt_standard"},
                "desc": {"type": "text", "analyzer": "rebuilt_standard"}
            }
        }
    }
