import os
import re
import glob
from pathlib import Path
from shutil import rmtree

import frontmatter

from config import Config

DIRNAME = Config.APP_PATH + "/data/"

# struct to create tree like file-structure
class Directory:
    def __init__(self, name):
        self.name = name
        self.child_files = []
        self.child_dirs = {}

# method from django to sanitize filename
def valid_filename(name):
    name = str(name).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", name)


def get_items(collections=[], path="", structured=True):
    datacont = None
    if structured:
        # for structured datacont
        datacont = Directory("root")
    else:
        # unstructured
        datacont = []
    if structured:
        for filename in glob.glob(DIRNAME + path + "**/*", recursive=True):
            paths = filename.split("/data/")[1].split("/")
            data = frontmatter.load(filename) if filename.endswith(".md") else None

            current_dir = datacont

            # iterate through paths
            for segment in paths:
                if segment.endswith(".md"):
                    current_dir.child_files.append(data)
                else:
                    # directory has not been saved in tree yet
                    if segment not in current_dir.child_dirs:
                        current_dir.child_dirs[segment] = Directory(segment)
                    current_dir = current_dir.child_dirs[segment]
    else:
        for filename in glob.glob(DIRNAME + path + "**/*.md", recursive=True):
            data = frontmatter.load(filename)
            if collections == [] or any(
                    [collection == data["type"] for collection in collections]):
                datacont.append(data)

    return datacont


def create(contents, title, path=""):
    with open(DIRNAME + path + "/" + valid_filename(title) + ".md", "w") as file:
        file.write(contents)


def get_item(dataobj_id):
    file = glob.glob(f"{DIRNAME}**/{dataobj_id}-*.md", recursive=True)[0]
    data = frontmatter.load(file)
    data["fullpath"] = os.getcwd() + "/" + file
    return data


def delete_item(id):
    file = glob.glob(f"{DIRNAME}**/{id}-*.md", recursive=True)[0]
    os.remove(file)


def get_dirs():
    dirnames = glob.glob(DIRNAME + "**/*", recursive=True)
    dirnames = [name.split("/data/")[1] for name in dirnames if not name.endswith(".md")]
    dirnames.append("not classified")
    return dirnames


def create_dir(name):
    sanitized_name = "/".join([valid_filename(pathname)
                               for pathname in name.split("/")])
    Path(DIRNAME + sanitized_name).mkdir(parents=True, exist_ok=True)


def delete_dir(name):
    try:
        rmtree(DIRNAME + name)
        return True
    except FileNotFoundError:
        return False
