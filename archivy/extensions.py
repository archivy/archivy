#!/usr/bin/env python
"""
Archivy: self-hosted knowledge repository that allows you to safely preserve
useful content that contributes to your knowledge bank.

Copyright (C) 2020 The Archivy Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys

import elasticsearch
from elasticsearch import Elasticsearch
from flask import current_app, g
from tinydb import TinyDB, Query, operations

from archivy.config import Config


def get_db():
    if 'db' not in g:
        g.db = TinyDB(
            os.path.join(
                current_app.config['APP_PATH'],
                'db.json'
            )
        )

    return g.db


def get_max_id():
    db = get_db()
    max_id = db.search(Query().name == "max_id")
    if not max_id:
        db.insert({"name": "max_id", "val": 0})
        return 0
    return max_id[0]["val"]


def set_max_id(val):
    db = get_db()
    db.update(operations.set("val", val), Query().name == "max_id")


def get_elastic_client():
    if not current_app.config['ELASTICSEARCH_ENABLED']:
        return None

    es = Elasticsearch(current_app.config['ELASTICSEARCH_URL'])
    try:
        health = es.cluster.health()
    except elasticsearch.exceptions.ConnectionError:
        current_app.logger.error(
            "Elasticsearch does not seem to be running on "
            f"{Config.ELASTICSEARCH_URL}. Please start "
            "it, for example with: sudo service elasticsearch restart"
        )
        current_app.logger.error(
            "You can disable Elasticsearch by setting the "
            "ELASTICSEARCH_ENABLED environment variable to 0"
        )
        sys.exit(1)

    if health["status"] not in ("yellow", "green"):
        current_app.logger.warning(
            "Elasticsearch reports that it is not working "
            "properly. Search might not work. You can disable "
            "Elasticsearch by setting ELASTICSEARCH_ENABLED to 0."
        )
    return es
