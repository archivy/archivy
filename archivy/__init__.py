from pathlib import Path
from threading import Thread

import elasticsearch
from flask import Flask

from archivy import extensions
from archivy.check_changes import run_watcher
from archivy.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# create dir that will hold data if it doesn't already exist
DIRNAME = app.config["APP_PATH"] + "/data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)

if app.config["ELASTICSEARCH_ENABLED"]:
    es = extensions.elastic_client()

    try:
        print(
            es.indices.create(
                index=app.config["INDEX_NAME"],
                body=app.config["ELASTIC_CONF"]))
    except elasticsearch.ElasticsearchException:
        print("Elasticsearch index already created")

    Thread(target=run_watcher).start()


app.jinja_options["extensions"].append("jinja2.ext.do")

from archivy import routes  # noqa:
