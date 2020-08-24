import elasticsearch
import subprocess
from pathlib import Path
from threading import Thread

from flask import Flask

from archivy import extensions
from archivy import data
from archivy.config import Config
from archivy.check_changes import run_watcher

app = Flask(__name__)
app.config.from_object(Config)

# create dir that will hold data if it doesn"t already exist
DIRNAME = app.config["APP_PATH"] + "/data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)

if app.config["ELASTICSEARCH_ENABLED"]:
    elastic_running = subprocess.run(
        "service elasticsearch status",
        shell=True,
        stdout=subprocess.DEVNULL).returncode
    if elastic_running != 0:
        print("Enter password to enable elasticsearch")
        subprocess.run("sudo service elasticsearch restart", shell=True)
    try:
        print(
            extensions.elastic_client().indices.create(
                index=app.config["INDEX_NAME"],
                body=app.config["ELASTIC_CONF"]))
    except elasticsearch.ElasticsearchException:
        print("Elasticsearch index already created")

    Thread(target=run_watcher).start()


app.jinja_options["extensions"].append("jinja2.ext.do")

from archivy import routes  # noqa:
