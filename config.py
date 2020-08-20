import os

class Config(object):
    ELASTICSEARCH_ENABLED = 0
    ELASTICSEARCH_URL = "http://localhost:9200"
    SECRET_KEY = os.urandom(32)
    INDEX_NAME = "dataobj"
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
