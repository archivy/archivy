import os

class Config(object):
    ELASTICSEARCH_ENABLED = os.environ.get("ELASTICSEARCH_ENABLED") or 0
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL") or "http://localhost:9200"
    SECRET_KEY = os.urandom(32)
    INDEX_NAME = "dataobj"
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

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
              "title":    { "type": "text", "analyzer": "rebuilt_standard" },  
              "tags":  { "type": "text", "analyzer": "rebuilt_standard"  }, 
              "body":   { "type": "text", "analyzer": "rebuilt_standard"  },
                  "desc": { "type": "text", "analyzer": "rebuilt_standard" }
            }
          }
        }
