import json
import subprocess
from pathlib import Path

import requests
from elasticsearch import Elasticsearch
from flask import Flask
from flask_scss import Scss
from tinydb import TinyDB

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
ELASTIC_SEARCH = None
INDEX_NAME = "dataobj"
if app.config['ELASTICSEARCH_ENABLED']:
    ELASTIC_SEARCH = Elasticsearch([app.config['ELASTICSEARCH_URL']])
    with open('elasticsearch.json', 'r') as search_data:
        elastic_conf = json.load(search_data)
        # create index if not already existing
        if not ELASTIC_SEARCH.indices.exists(INDEX_NAME):
            print(ELASTIC_SEARCH.indices.create(index=INDEX_NAME, body=elastic_conf))

# create dir that will hold data if it doesn't already exist
DIRNAME = "data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)
db = TinyDB("db.json")
app.config['max_id'] = 0
app.jinja_options['extensions'].append('jinja2.ext.do')
Scss(app)


from main import data
from main import routes, models

for dataobj in data.get_items(structured=False):
    app.config['max_id'] = max(app.config['max_id'], dataobj['id'])
app.config['max_id'] += 1

