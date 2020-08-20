#!/usr/bin/python3
from main import search, models
import frontmatter
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ModifHandler(FileSystemEventHandler):

    def on_modified(self, event):
        if event.src_path.endswith(
                ".md"):
            print(f"Changes to {event.src_path}")
            dataobj = models.DataObj.from_file(event.src_path)
            search.add_to_index("dataobj", dataobj)
            self.last_modify_event = event.src_path

    def on_deleted(self, event):
        if event.src_path.endswith(".md"):
            id = event.src_path.split("/")[-1].split("-")[0]
            search.remove_from_index("dataobj", id)
            print(f"{event.src_path} has been removed")
            self.last_delete_event = event.src_path

def run_watcher():
    event_handler = ModifHandler()
    observer = Observer()
    observer.schedule(event_handler, path="data/", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
