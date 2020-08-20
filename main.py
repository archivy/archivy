import os
from dotenv import load_dotenv

from archivy import app


def run():
    load_dotenv()
    app.run()
