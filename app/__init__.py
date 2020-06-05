from flask import Flask
from flask_scss import Scss
from config import Config
import os
import tinydb

app = Flask(__name__)
app.config.from_object(Config)

Scss(app)
db = tinydb.TinyDB("db.json")

from app import routes, models
