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
import appdirs


class Config(object):
    ELASTICSEARCH_ENABLED = int(os.environ.get("ELASTICSEARCH_ENABLED") or 0)
    ELASTICSEARCH_URL = os.environ.get(
        "ELASTICSEARCH_URL") or "http://localhost:9200"
    SECRET_KEY = os.urandom(32)
    INDEX_NAME = "dataobj"
    APP_PATH = \
        os.getenv('ARCHIVY_DATA_DIR') or appdirs.user_data_dir('archivy')
    os.makedirs(APP_PATH, exist_ok=True)

    PANDOC_HIGHLIGHT_THEME = os.environ.get("PANDOC_THEME") or "pygments"
    ELASTIC_CONF = {
        "settings": {
            "highlight": {
                "max_analyzed_offset": 100000000
            },
            "analysis": {
                "analyzer": {
                    "rebuilt_standard": {
                        "stopwords": "_english_",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "kstem",
                            "trim",
                            "unique"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "rebuilt_standard",
                    "term_vector": "with_positions_offsets"
                },
                "tags": {"type": "text", "analyzer": "rebuilt_standard"},
                "body": {"type": "text", "analyzer": "rebuilt_standard"},
                "desc": {"type": "text", "analyzer": "rebuilt_standard"}
            }
        }
    }
