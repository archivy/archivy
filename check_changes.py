#!/usr/bin/python3
from main import search, models
import frontmatter
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ModifHandler(FileSystemEventHandler):
    last_event = ''

    def on_modified(self, event):
        if event.src_path != self.last_event and event.src_path.endswith(
                ".md"):
            print(f"Changes to {event.src_path}")
            dataobj = models.DataObj.from_file(event.src_path)
            search.add_to_index('dataobj', dataobj)
            last_event = event.src_path


if __name__ == "__main__":
    event_handler = ModifHandler()
    observer = Observer()
    observer.schedule(event_handler, path='data/', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
