import os
import glob
import platform
import subprocess
from pathlib import Path
from shutil import rmtree

import frontmatter
from flask import current_app
from werkzeug.utils import secure_filename


SEP = os.path.sep


# FIXME: ugly hack to make sure the app path is evaluated at the right time
def get_data_dir():
    return os.path.join(current_app.config['APP_PATH'], "data" + SEP)


# struct to create tree like file-structure
class Directory:
    def __init__(self, name):
        self.name = name
        self.child_files = []
        self.child_dirs = {}


FILE_GLOB = "-[0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*"


def get_by_id(dataobj_id):
    results = glob.glob(f"{get_data_dir()}**{SEP}{dataobj_id}{FILE_GLOB}", recursive=True)
    return results[0] if results else None


def get_items(collections=[], path="", structured=True, json_format=False):
    datacont = Directory("root") if structured else []
    if structured:
        for filename in glob.glob(get_data_dir() + path + f"**{SEP}*",
                                  recursive=True):
            paths = filename.split(f"{SEP}data{SEP}")[1].split(SEP)

            if filename.endswith(".md"):
                data = frontmatter.load(filename)
            data = frontmatter.load(
                filename) if filename.endswith(".md") else None

            current_dir = datacont

            # iterate through paths
            for segment in paths:
                if segment.endswith(".md") or segment.endswith(".epub"):
                    current_dir.child_files.append(data)
                else:
                    # directory has not been saved in tree yet
                    if segment not in current_dir.child_dirs:
                        current_dir.child_dirs[segment] = Directory(segment)
                    current_dir = current_dir.child_dirs[segment]
    else:
        for filename in glob.glob(f"{get_data_dir()}{path}**{SEP}[0-9]*{FILE_GLOB}",
                                  recursive=True):
            data = frontmatter.load(filename)
            if len(collections) == 0 or \
                    any([collection == data["type"]
                        for collection in collections]):
                if json_format:
                    dict_dataobj = data.__dict__
                    # remove unnecessary yaml handler
                    dict_dataobj.pop("handler")
                    datacont.append(dict_dataobj)
                else:
                    datacont.append(data)
    return datacont


def create(contents, title, path="", needs_to_open=False):
    path_to_md_file = os.path.join(
        get_data_dir(), path, "{}.md".format(secure_filename(title)))
    with open(path_to_md_file, "w") as file:
        file.write(contents)

    if needs_to_open and not current_app.config["TESTING"]:
        open_file(path_to_md_file)
    return path_to_md_file


def get_item(dataobj_id):
    file = get_by_id(dataobj_id)
    if file:
        data = frontmatter.load(file)
        data["fullpath"] = file
        return data
    return None


def delete_item(dataobj_id):
    file = get_by_id(dataobj_id)

    if file:
        os.remove(file)


def get_dirs():
    dirnames = glob.glob(get_data_dir() + f"**{SEP}*", recursive=True)

    # parse dirnames into relative paths
    dirnames = [name.split("{SEP}data{SEP}")[1]
                for name in dirnames if not name.endswith(".md")]

    # append name for root dir
    dirnames.append("not classified")
    return dirnames


def create_dir(name):
    sanitized_name = SEP.join([secure_filename(pathname)
                               for pathname in name])
    Path(get_data_dir() + sanitized_name).mkdir(parents=True)
    return sanitized_name


def delete_dir(name):
    try:
        rmtree(get_data_dir() + name)
        return True
    except FileNotFoundError:
        return False


def open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
