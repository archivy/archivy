import os
import appdirs


class Config(object):
    """Configuration object for the application"""

    def __init__(self):
        self.SECRET_KEY = os.urandom(32)
        self.PORT = 5000
        self.HOST = "127.0.0.1"

        overridden_internal_dir = os.environ.get("ARCHIVY_INTERNAL_DIR_PATH")
        self.INTERNAL_DIR = overridden_internal_dir or appdirs.user_data_dir("archivy")

        self.USER_DIR = self.INTERNAL_DIR
        self.DEFAULT_BOOKMARKS_DIR = ""
        self.SITE_TITLE = "Archivy"
        os.makedirs(self.INTERNAL_DIR, exist_ok=True)

        self.PANDOC_HIGHLIGHT_THEME = "pygments"
        self.SCRAPING_CONF = {"save_images": False}

        self.THEME_CONF = {
            "use_theme_dark": False,
            "use_custom_css": False,
            "custom_css_file": "",
        }

        self.EDITOR_CONF = {
            "settings": {
                "html": False,
                "xhtmlOut": False,
                "breaks": False,
                "linkify": True,
                "typographer": False,
            },
            "plugins": {
                "markdownitFootnote": {},
                "markdownitMark": {},
                "markdownItAnchor": {"permalink": True, "permalinkSymbol": "¶"},
                "markdownItTocDoneRight": {},
            },
        }

        self.SEARCH_CONF = {
            "enabled": 0,
            "url": "http://localhost:9200",
            "index_name": "dataobj",
            "engine": "",
            "es_user": "",
            "es_password": "",
            "es_processing_conf": {
                "settings": {
                    "highlight": {"max_analyzed_offset": 100000000},
                    "analysis": {
                        "analyzer": {
                            "rebuilt_standard": {
                                "stopwords": "_english_",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "kstem", "trim", "unique"],
                            }
                        }
                    },
                },
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": "rebuilt_standard",
                            "term_vector": "with_positions_offsets",
                        },
                        "tags": {"type": "text", "analyzer": "rebuilt_standard"},
                        "body": {"type": "text", "analyzer": "rebuilt_standard"},
                    }
                },
            },
        }

    def override(self, user_conf: dict, nested_dict=None):
        """
        This function enables an override of the default configuration with user values.

        Acts smartly so as to only set options already set in the default config.

        - user_conf: current (nested) dictionary of user config key/values
        - nested_dict: reference to the current object that should be modified.
            If none it's just a reference to the current Config itself, otherwise it's a nested dict of the Config
        """
        for k, v in user_conf.items():
            if (nested_dict and not k in nested_dict) or (
                not nested_dict and not hasattr(self, k)
            ):
                # check the key is indeed defined in our defaults
                continue
            curr_default_val = nested_dict[k] if nested_dict else getattr(self, k)
            if type(v) is dict:
                # pass on override to sub configuration dictionary if the current type of value being traversed is dict
                self.override(v, curr_default_val)
            else:
                # otherwise just set
                if type(curr_default_val) == list and type(v) == str:
                    v = v.split(", ")
                if nested_dict:
                    nested_dict[k] = v
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
