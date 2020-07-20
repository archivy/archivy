from pathlib import Path
from flask import Flask
from flask_scss import Scss
from elasticsearch import Elasticsearch
from tinydb import TinyDB
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
ELASTIC_SEARCH = Elasticsearch(
    [app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_ENABLED'] else None

# create dir that will hold data if it doesn't already exist
DIRNAME = "data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)
db = TinyDB("db.json")
app.config['MAX_ID'] = 0
app.jinja_options['extensions'].append('jinja2.ext.do')
Scss(app)

from main import data
from main import routes, models
for dataobj in data.get_items(structured=False):
    app.config['MAX_ID'] = max(app.config['MAX_ID'], dataobj['id'])
app.config['MAX_ID'] += 1


