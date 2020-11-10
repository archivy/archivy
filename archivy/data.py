import platform
import subprocess
import os
from pathlib import Path
from shutil import rmtree

import frontmatter
from flask import current_app
from werkzeug.utils import secure_filename


# FIXME: ugly hack to make sure the app path is evaluated at the right time
def get_data_dir():
    return Path(current_app.config['APP_PATH']) / "data"


# struct to create tree like file-structure
class Directory:
    def __init__(self, name):
        self.name = name
        self.child_files = []
        self.child_dirs = {}


FILE_GLOB = "-[0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*"


def get_by_id(dataobj_id):
    results = list(get_data_dir().rglob(f"{dataobj_id}{FILE_GLOB}"))
    return results[0] if results else None


def get_items(collections=[], path="", structured=True, json_format=False):
    datacont = Directory("root") if structured else []
    home_dir = get_data_dir()
    for filename in home_dir.rglob(path + "*"):
        if structured:
            paths = filename.relative_to(home_dir)
            current_dir = datacont

            # iterate through paths
            for segment in paths.parts:
                if segment.endswith(".md"):
                    data = frontmatter.load(filename)
                    current_dir.child_files.append(data)
                else:
                    # directory has not been saved in tree yet
                    if segment not in current_dir.child_dirs:
                        current_dir.child_dirs[segment] = Directory(segment)
                    current_dir = current_dir.child_dirs[segment]
        else:
            if filename.parts[-1].endswith(".md"):
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


def create(contents, title, path=""):
    path_to_md_file = get_data_dir() / path / f"{secure_filename(title)}.md"
    with open(path_to_md_file, "w", encoding="utf-8") as file:
        file.write(contents)

    return path_to_md_file


def get_item(dataobj_id):
    file = get_by_id(dataobj_id)
    if file:
        data = frontmatter.load(file)
        data["fullpath"] = str(file)
        return data
    return None


def delete_item(dataobj_id):
    file = get_by_id(dataobj_id)

    if file:
        Path(file).unlink()


def get_dirs():
    # join glob matchers
    dirnames = [str(dir_path.relative_to(get_data_dir())) for dir_path
                in get_data_dir().rglob("*") if dir_path.is_dir()]

    # append name for root dir
    dirnames.append("not classified")
    return dirnames


def create_dir(name):
    home_dir = get_data_dir()
    new_path = home_dir / name
    new_path.mkdir(parents=True, exist_ok=True)
    return str(new_path.relative_to(home_dir))


def delete_dir(name):
    try:
        rmtree(get_data_dir() / name)
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
