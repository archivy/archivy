from flask import Flask
from flask_scss import Scss
from config import Config
import os
import tinydb
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object(Config)
ELASTIC_SEARCH = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None

Scss(app)
db = tinydb.TinyDB("db.json")

from app import routes, models
