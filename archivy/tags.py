from flask import current_app
from archivy import data, search


def build_index_from_scratch():
    print(data.get_items())
