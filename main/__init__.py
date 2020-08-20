import json
import subprocess
from pathlib import Path
from threading import Thread

import requests
from elasticsearch import Elasticsearch
from flask import Flask
from flask_scss import Scss
from tinydb import TinyDB, Query

from main import extensions
from config import Config
from check_changes import run_watcher

app = Flask(__name__)
app.config.from_object(Config)

if app.config["ELASTICSEARCH_ENABLED"]:

    elastic_running = subprocess.run("service elasticsearch status", shell=True, stdout=subprocess.DEVNULL).returncode
    if elastic_running != 0:
        print("Enter password to enable elasticsearch")
        subprocess.run("sudo service elasticsearch restart", shell=True) 
    
    with open("elasticsearch.json", "r") as search_data:
        elastic_conf = json.load(search_data)
        # create index if not already existing
        try:
            print(extensions.elastic_client().indices.create(index=app.config["INDEX_NAME"], body=elastic_conf))
        except:
            print("Elasticsearch index already created")

    Thread(target=run_watcher).start()


app.jinja_options["extensions"].append("jinja2.ext.do")

Scss(app)

# create dir that will hold data if it doesn"t already exist
DIRNAME = "data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)


from main import data

# get max id
cur_id = extensions.get_max_id()
for dataobj in data.get_items(structured=False):
    cur_id = max(cur_id, dataobj["id"])

extensions.set_max_id(cur_id)

from main import routes, models
