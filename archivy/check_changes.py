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
        self.ELASTIC = app.config["ELASTICSEARCH_ENABLED"]
        self.data_dir = os.path.join(app.config["APP_PATH"], "data" + SEP)
        self.last_formatted = ""
        self.time_formatted = time.time()

    def is_unformatted(self, filename):
        return (not re.match(DATAOBJ_REGEX, filename)
                and not filename.startswith(".")
                and filename.endswith(".md"))

    def format_file(self, filepath):
        # weird buggy errors with watchdog where event is triggered twice
        if filepath == self.last_formatted and time.time() - self.time_formatted <= 40:
            return

        try:
            file_contents = open(filepath, "r").read()
        except FileNotFoundError:
            return

        # extract name of file
        split_path = filepath.replace(self.data_dir, "").split(SEP)
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

        self.last_formatted = filepath
        self.time_formatted = time.time()
        try:
            os.remove(filepath)
        except FileNotFoundError:
            return

    def on_modified(self, event):
        with self.app.app_context():
            filename = event.src_path.split(SEP)[-1]
            if re.match(DATAOBJ_REGEX, filename) and self.ELASTIC:
                self.app.logger.info(f"Detected changes to {event.src_path}")
                dataobj = models.DataObj.from_file(event.src_path)
                if dataobj.validate():
                    search.add_to_index(self.app.config['INDEX_NAME'], dataobj)
            elif self.is_unformatted(filename):
                self.format_file(event.src_path)

    def on_deleted(self, event):
        with self.app.app_context():
            filename = event.src_path.split(SEP)[-1]
            if (re.match(DATAOBJ_REGEX, filename)
                    and self.ELASTIC):
                id = event.src_path.split(SEP)[-1].split("-")[0]
                search.remove_from_index(self.app.config['INDEX_NAME'], id)
                self.app.logger.info(f"{event.src_path} has been removed")

    def on_created(self, event):
        with self.app.app_context():
            filename = event.src_path.split(SEP)[-1]
            # check file is not formatted and is md file and is not temp file
            if self.is_unformatted(filename):
                self.format_file(event.src_path)


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
            path=os.path.join(
                self.app.config['APP_PATH'],
                'data' + SEP
            ),
            recursive=True)
        observer.start()

        while self.running:
            time.sleep(1)
        observer.stop()
        observer.join()

    def stop(self):
        self.running = False
