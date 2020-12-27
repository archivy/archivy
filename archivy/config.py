import os
import appdirs


class Config(object):
    """Configuration object for the application"""

    def __init__(self):
        self.SECRET_KEY = os.urandom(32)
        self.PORT = 5000
        self.HOST = "127.0.0.1"
        self.INTERNAL_DIR = appdirs.user_data_dir("archivy")
        self.USER_DIR = self.INTERNAL_DIR
        os.makedirs(self.INTERNAL_DIR, exist_ok=True)

        self.PANDOC_HIGHLIGHT_THEME = "pygments"

        self.SEARCH_CONF = {
                "enabled": 0,
                "url": "http://localhost:9200",
                "index_name": "dataobj",
                "search_conf": {
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
                        }
                    }
                }
            }

    def override(self, user_conf: dict):
        for k, v in user_conf.items():
            # handle ES options, don't override entire dict if one key is passed
            if k == "SEARCH_CONF":
                for subkey, subval in v.items():
                    self.SEARCH_CONF[subkey] = subval
            else:
                setattr(self, k, v)


class BaseHooks:
    """
    Class of methods users can inherit to configure and extend archivy with hooks.


    ## Usage:

    Archivy checks for the presence of a `hooks.py` file in the
    user directory that stores the `data/` directory with your notes and bookmarks.
    This location is usually set during `archivy init`.

    Example `hooks.py` file:

    ```python
    from archivy.config import BaseHooks

    class Hooks(BaseHooks):
        def on_edit(self, dataobj):
            print(f"Edit made to {dataobj.title}")

        def before_dataobj_create(self, dataobj):
            from random import randint
            dataobj.content += f"\\nThis note's random number is {randint(1, 10)}"

        # ...
    ```

    If you have ideas for any other hooks you'd find useful if they were supported,
    please open an [issue](https://github.com/archivy/archivy/issues).
    """

    def on_dataobj_create(self, dataobj):
        """Hook for dataobj creation."""

    def before_dataobj_create(self, dataobj):
        """Hook called immediately before dataobj creation."""

    def on_user_create(self, user):
        """Hook called after a new user is created."""

    def on_edit(self, dataobj):
        """Hook called whenever a user edits through the web interface or the API."""
