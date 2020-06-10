import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    
