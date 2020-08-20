import json
import subprocess
from pathlib import Path

import requests
from elasticsearch import Elasticsearch
from flask import Flask
from flask_scss import Scss
from tinydb import TinyDB, Query

from main import extensions
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

if extensions.ELASTICSEARCH:
    with open("elasticsearch.json", "r") as search_data:
        elastic_conf = json.load(search_data)
        # create index if not already existing
        try:
            print(extensions.ELASTIC_SEARCH.indices.create(index=app.config["INDEX_NAME"], body=elastic_conf))
        except:
            print("Elasticsearch index already created")


app.jinja_options["extensions"].append("jinja2.ext.do")

Scss(app)

# create dir that will hold data if it doesn"t already exist
DIRNAME = "data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)


from main import data
from main import routes, models

# get max id
cur_id = extensions.get_max_id()
for dataobj in data.get_items(structured=False):
    cur_id = max(cur_id, dataobj["id"])

extensions.set_max_id(cur_id)
