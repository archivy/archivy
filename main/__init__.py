from flask import Flask
from flask_scss import Scss
from config import Config
from pathlib import Path
from elasticsearch import Elasticsearch
from tinydb import TinyDB
app = Flask(__name__)
app.config.from_object(Config)
ELASTIC_SEARCH = Elasticsearch(
    [app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_ENABLED'] else None

# create dir that will hold data if it doesn't already exist
dirname = "data/"
Path(dirname).mkdir(parents=True, exist_ok=True)
db = TinyDB("db.json")
app.config['MAX_ID'] = 0
app.jinja_options['extensions'].append('jinja2.ext.do')
Scss(app)

from main import routes, models
from main import data
for dataobj in data.get_items(structured=False):
    app.config['MAX_ID'] = max(app.config['MAX_ID'], dataobj['id'])
app.config['MAX_ID'] += 1
