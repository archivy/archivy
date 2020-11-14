import logging
import sys
from pathlib import Path

import elasticsearch
import pypandoc
from flask import Flask
from flask_login import LoginManager
from secrets import token_urlsafe
from tinydb import Query

from archivy import helpers
from archivy.models import User
from archivy.api import api_bp
from archivy.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(logging.INFO)

# check if pandoc is installed, otherwise install
try:
    pypandoc.get_pandoc_version()
except OSError:
    app.logger.error("Pandoc installation not found.\n"
                     + "Please install it at https://pandoc.org/installing.html")
    sys.exit(1)

# create dir that will hold data if it doesn't already exist
DIRNAME = app.config["APP_PATH"] + "/data/"
Path(DIRNAME).mkdir(parents=True, exist_ok=True)

if app.config["ELASTICSEARCH_ENABLED"]:
    with app.app_context():
        es = helpers.get_elastic_client()
        try:
            es.indices.create(
                index=app.config["INDEX_NAME"],
                body=app.config["ELASTIC_CONF"])
        except elasticsearch.ElasticsearchException:
            app.logger.info("Elasticsearch index already created")


# login routes / setup
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
app.register_blueprint(api_bp, url_prefix='/api')


@login_manager.user_loader
def load_user(user_id):
    db = helpers.get_db()
    res = db.get(doc_id=int(user_id))
    if res and res["type"] == "user":
        return User.from_db(res)
    return None


app.jinja_options["extensions"].append("jinja2.ext.do")

# create admin user if it does not exist
with app.app_context():
    db = helpers.get_db()
    user_query = Query()
    # noqa here because tinydb requires us to explicitly specify is_admin == True
    if not db.search((user_query.type == "user") & (user_query.is_admin == True)): # noqa:
        password = token_urlsafe(32)
        user = User(username="admin", password=password, is_admin=True)
        if user.insert():
            app.logger.info(f"""Archivy has created an admin user as it did not exist.
                            Username: 'admin', password: '{password}'
                        """)

from archivy import routes  # noqa:
