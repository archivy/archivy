import logging
from pathlib import Path
from json import dumps

from flask import Flask
from flask_compress import Compress
from flask_login import LoginManager

from archivy import helpers
from archivy.api import api_bp
from archivy.config import Config
from archivy.data import get_items
from archivy.models import User
from archivy.helpers import load_config
from archivy.search import create_lunr_index, create_es_index

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
        if app.config["SEARCH_CONF"]["engine"] == "elasticsearch":
            create_es_index()
        else:
            index = create_lunr_index(documents=get_items(structured=False))
            with (Path(app.config["INTERNAL_DIR"]) / "index.json").open("w") as f:
                f.write(dumps(index.serialize()))


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

from archivy import routes  # noqa:
