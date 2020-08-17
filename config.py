import os

class Config(object):
    ELASTICSEARCH_ENABLED = int(os.environ.get('ELASTICSEARCH_ENABLED') or 0)
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    SECRET_KEY = os.urandom(32)
    max_id = 0
