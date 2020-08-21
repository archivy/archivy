import json
import subprocess
from pathlib import Path
from threading import Thread

import requests
from elasticsearch import Elasticsearch
from flask import Flask
from flask_scss import Scss
from tinydb import TinyDB, Query

from archivy import extensions
from archivy.config import Config
from archivy.check_changes import run_watcher

app = Flask(__name__)
app.config.from_object(Config)

# create dir that will hold data if it doesn"t already exist
DIRNAME = app.config["APP_PATH"] + "/data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)

if app.config["ELASTICSEARCH_ENABLED"]:
    elastic_running = subprocess.run("service elasticsearch status", shell=True, stdout=subprocess.DEVNULL).returncode
    if elastic_running != 0:
        print("Enter password to enable elasticsearch")
        subprocess.run("sudo service elasticsearch restart", shell=True) 
    try:
        print(extensions.elastic_client().indices.create(index=app.config["INDEX_NAME"], body=app.config["ELASTIC_CONF"]))
    except Exception as e:
        print("Elasticsearch index already created")

    Thread(target=run_watcher).start()


app.jinja_options["extensions"].append("jinja2.ext.do")

Scss(app)



from archivy import data

# get max id
cur_id = 1
for dataobj in data.get_items(structured=False):
    cur_id = max(cur_id, dataobj["id"])

extensions.set_max_id(cur_id + 1)

from archivy import routes, models
