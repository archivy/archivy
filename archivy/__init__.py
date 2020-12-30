import logging
from pathlib import Path

import elasticsearch
from flask import Flask
from flask_compress import Compress
from flask_login import LoginManager

from archivy import helpers
from archivy.api import api_bp
from archivy.models import User
from archivy.config import Config
from archivy.helpers import load_config

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
config = Config()
try:
    # if it exists, load user config
    config.override(load_config(config.INTERNAL_DIR))
except FileNotFoundError:
    pass

app.config.from_object(config)

(Path(app.config["USER_DIR"]) / "data").mkdir(parents=True, exist_ok=True)

if app.config["SEARCH_CONF"]["enabled"]:
    with app.app_context():
        es = helpers.get_elastic_client()
        try:
            es.indices.create(
                index=app.config["SEARCH_CONF"]["index_name"],
                body=app.config["SEARCH_CONF"]["search_conf"])
        except elasticsearch.exceptions.RequestError:
            app.logger.info("Elasticsearch index already created")


# login routes / setup
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
app.register_blueprint(api_bp, url_prefix='/api')

# compress files
Compress(app)


@login_manager.user_loader
def load_user(user_id):
    db = helpers.get_db()
    res = db.get(doc_id=int(user_id))
    if res and res["type"] == "user":
        return User.from_db(res)
    return None


app.jinja_options["extensions"].append("jinja2.ext.do")


@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    else:
        return plural

from archivy import routes  # noqa:
