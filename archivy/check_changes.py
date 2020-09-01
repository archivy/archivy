import os
import re
import time

import flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from archivy import search, models

DATAOBJ_REGEX = re.compile(r"^\d+-\d{2}-\d{2}-\d{2}-.*\.md$")


class ModifHandler(FileSystemEventHandler):
    def __init__(self, app: flask.Flask):
        self.app = app
        self.ELASTIC = app.config["ELASTICSEARCH_ENABLED"]
        self.data_dir = os.path.join(app.config["APP_PATH"], "data/")

    def format_file(self, filepath):
        # weird buggy errors with watchdog
        try:
            file_contents = open(filepath, "r").read()
        except FileNotFoundError:
            return
        # extract name of file
        split_path = filepath.replace(self.data_dir, "").split("/")
        file_title = split_path[-1].split(".")[0]
        directory = "/".join(split_path[0:-1])
        note_dataobj = {
                "title": file_title,
                "content": file_contents,
                "type": "note",
                "path": directory
            }

        dataobj = models.DataObj(**note_dataobj)
        dataobj.insert()
        try:
            os.remove(filepath)
        except FileNotFoundError:
            return

    def on_modified(self, event):
        with self.app.app_context():
            filename = event.src_path.split("/")[-1]
            if re.match(DATAOBJ_REGEX, filename) and self.ELASTIC:
                self.app.logger.info(f"Detected changes to {event.src_path}")
                dataobj = models.DataObj.from_file(event.src_path)
                search.add_to_index(self.app.config['INDEX_NAME'], dataobj)
            elif (not re.match(DATAOBJ_REGEX, filename) and
                    event.src_path.endswith(".md")):
                self.format_file(event.src_path)

    def on_deleted(self, event):
        with self.app.app_context():
            filename = event.src_path.split("/")[-1]
            if (re.match(DATAOBJ_REGEX, filename)
                    and self.ELASTIC):
                id = event.src_path.split("/")[-1].split("-")[0]
                search.remove_from_index(self.app.config['INDEX_NAME'], id)
                self.app.logger.info(f"{event.src_path} has been removed")

    def on_created(self, event):
        with self.app.app_context():
            filename = event.src_path.split("/")[-1]
            if (not re.match(DATAOBJ_REGEX, filename)
                    and filename.endswith(".md")):
                self.format_file(event.src_path)


def run_watcher(app):
    event_handler = ModifHandler(app)
    observer = Observer()
    observer.schedule(
        event_handler,
        path=os.path.join(
            app.config['APP_PATH'],
            'data/'
        ),
        recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
