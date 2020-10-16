import logging
from pathlib import Path

import elasticsearch
from flask import Flask
import pypandoc

from archivy import extensions
from archivy.api import api_bp
from archivy.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(logging.INFO)
app.register_blueprint(api_bp, url_prefix='/api')


# check if pandoc is installed, otherwise install
try:
    pypandoc.get_pandoc_version()
except OSError:
    app.logger.info("Installing pandoc")
    pypandoc.download_pandoc()

# create dir that will hold data if it doesn't already exist
DIRNAME = app.config["APP_PATH"] + "/data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)

if app.config["ELASTICSEARCH_ENABLED"]:
    with app.app_context():
        es = extensions.get_elastic_client()
        try:
            es.indices.create(
                index=app.config["INDEX_NAME"],
                body=app.config["ELASTIC_CONF"])
        except elasticsearch.ElasticsearchException:
            app.logger.info("Elasticsearch index already created")


app.jinja_options["extensions"].append("jinja2.ext.do")

from archivy import routes  # noqa:
