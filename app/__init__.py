from flask import Flask
from flask_scss import Scss
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Scss(app)

from app import routes
