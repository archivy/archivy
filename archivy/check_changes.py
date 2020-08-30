import os
import re
import time

import flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from archivy import search, models

DATAOBJ_REGEX = re.compile("^\d+-\d{2}-\d{2}-\d{2}-.*\.md$")

class ModifHandler(FileSystemEventHandler):
    def __init__(self, app: flask.Flask):
        self.app = app

    def on_modified(self, event):
        with self.app.app_context():
            filename = event.src_path.split("/")[-1]
            if re.match(DATAOBJ_REGEX, filename):
                self.app.logger.info(f"Detected changes to {event.src_path}")
                dataobj = models.DataObj.from_file(event.src_path)
                search.add_to_index(self.app.config['INDEX_NAME'], dataobj)
                self.last_modify_event = event.src_path

    def on_deleted(self, event):
        with self.app.app_context():
            filename = event.src_path.split("/")[-1]
            if re.match(DATAOBJ_REGEX, filename):
                id = event.src_path.split("/")[-1].split("-")[0]
                search.remove_from_index(self.app.config['INDEX_NAME'], id)
                self.app.logger.info(f"{event.src_path} has been removed")
                self.last_delete_event = event.src_path


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
