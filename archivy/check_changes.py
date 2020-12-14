import os
import re
import time
from threading import Thread

import flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from archivy import search, models

DATAOBJ_REGEX = re.compile(r"^\d+-\d{2}-\d{2}-\d{2}-.*\.md$")
SEP = os.path.sep


class ModifHandler(FileSystemEventHandler):
    def __init__(self, app: flask.Flask):
        self.app = app
        self.app.logger.info("Running watcher")
        self.ELASTIC = app.config["SEARCH_CONF"]["enabled"]
        self.data_dir = os.path.join(app.config["USER_DIR"], "data" + SEP)

    def on_modified(self, event):
        with self.app.app_context():
            filename = event.src_path.split(SEP)[-1]
            if re.match(DATAOBJ_REGEX, filename) and self.ELASTIC:
                self.app.logger.info(f"Detected changes to {event.src_path}")
                with open(event.src_path) as f:
                    dataobj = models.DataObj.from_md(f.read())
                if dataobj.validate():
                    search.add_to_index(
                            dataobj)

    def on_deleted(self, event):
        with self.app.app_context():
            filename = event.src_path.split(SEP)[-1]
            print(filename)
            if (re.match(DATAOBJ_REGEX, filename)
                    and self.ELASTIC):
                id = event.src_path.split(SEP)[-1].split("-")[0]
                search.remove_from_index(id)
                self.app.logger.info(f"{event.src_path} has been removed")


class Watcher(Thread):

    def __init__(self, app):
        self.running = True
        self.app = app
        Thread.__init__(self)

    def run(self):
        event_handler = ModifHandler(self.app)
        observer = Observer()
        observer.schedule(
            event_handler,
            path=event_handler.data_dir,
            recursive=True)
        observer.start()

        while self.running:
            time.sleep(1)
        observer.stop()
        observer.join()

    def stop(self):
        self.running = False
