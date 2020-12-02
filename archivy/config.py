import os
import appdirs


class Config(object):
    """Configuration object for the application"""

    def __init__(self):
        self.SECRET_KEY = os.urandom(32)
        self.PORT = 5000
        self.INTERNAL_DIR = appdirs.user_data_dir("archivy")
        self.USER_DIR = self.INTERNAL_DIR
        os.makedirs(self.INTERNAL_DIR, exist_ok=True)

        self.PANDOC_HIGHLIGHT_THEME = "pygments"

        self.ELASTICSEARCH_CONF = {
                "enabled": 0,
                "url": "http://localhost:9200",
                "index_name": "dataobj",
                "search_conf": {
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
            }

    def override(self, user_conf: dict):
        for k, v in user_conf.items():
            # handle ES options, don't override entire dict if one key is passed
            if k == "ELASTICSEARCH_CONF":
                for subkey, subval in v.items():
                    self.ELASTICSEARCH_CONF[subkey] = subval
            else:
                setattr(self, k, v)
