import platform
import subprocess
import os
from pathlib import Path
from shutil import rmtree

import frontmatter
from flask import current_app
from werkzeug.utils import secure_filename

from archivy.helpers import load_hooks
from archivy.search import remove_from_index


# FIXME: ugly hack to make sure the app path is evaluated at the right time
def get_data_dir():
    """Returns the directory where dataobjs are stored"""
    return Path(current_app.config['USER_DIR']) / "data"


def is_relative_to(sub_path, parent):
    """Implement pathlib `is_relative_to` only available in python 3.9"""
    try:
        sub_path.resolve().relative_to(parent)
        return True
    except ValueError:
        return False


class Directory:
    """Tree like file-structure used to build file navigation in Archiv"""
    def __init__(self, name):
        self.name = name
        self.child_files = []
        self.child_dirs = {}


FILE_GLOB = "[0-9]*-*.md"


def get_by_id(dataobj_id):
    """Returns filename of dataobj of given id"""
    results = list(get_data_dir().rglob(f"{dataobj_id}-*.md"))
    return results[0] if results else None


def get_items(collections=[], path="", structured=True, json_format=False):
    """
    Gets all dataobjs.

    Parameters:

    - **collections** - filter dataobj by type, eg. bookmark / note
    - **path** - filter by path
    - **structured: if set to True, will return a Directory object, otherwise
      data will just be returned as a list of dataobjs
    - **json_format**: boolean value used internally to pre-process dataobjs
      to send back a json response.
    """
    datacont = Directory(path or "root") if structured else []
    data_dir = get_data_dir()
    root_dir = data_dir / path
    if not is_relative_to(root_dir, data_dir) or not root_dir.exists():
        raise FileNotFoundError
    if structured:
        for filepath in root_dir.rglob("*"):
            current_path = filepath.relative_to(root_dir)
            current_dir = datacont

            # iterate through parent directories
            for segment in current_path.parts[:-1]:
                # directory has not been saved in tree yet
                if segment not in current_dir.child_dirs:
                    current_dir.child_dirs[segment] = Directory(segment)
                current_dir = current_dir.child_dirs[segment]

            # handle last part of current_path
            last_seg = current_path.parts[-1]
            if filepath.is_dir():
                if last_seg not in current_dir.child_dirs:
                    current_dir.child_dirs[last_seg] = Directory(last_seg)
                current_dir = current_dir.child_dirs[last_seg]
            elif last_seg.endswith(".md"):
                data = frontmatter.load(filepath)
                current_dir.child_files.append(data)
    else:
        for filepath in root_dir.rglob("*.md"):
            data = frontmatter.load(filepath)
            data["fullpath"] = str(filepath.parent.relative_to(root_dir))
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
    """
    Helper method to save a new dataobj onto the filesystem.

    Parameters:

    - **contents**: md file contents
    - **title** - title used for filename
    - **path**
    """
    path_to_md_file = get_data_dir() / path.strip("/") / f"{secure_filename(title)}.md"
    with open(path_to_md_file, "w", encoding="utf-8") as file:
        file.write(contents)

    return path_to_md_file


def get_item(dataobj_id):
    """Returns a Post object with the given dataobjs' attributes"""
    file = get_by_id(dataobj_id)
    if file:
        data = frontmatter.load(file)
        data["fullpath"] = str(file)
        data["dir"] = str(file.parent.relative_to(get_data_dir()))
        return data
    return None


def delete_item(dataobj_id):
    """Delete dataobj of given id"""
    file = get_by_id(dataobj_id)
    remove_from_index(dataobj_id)
    if file:
        Path(file).unlink()


def update_item(dataobj_id, new_content):
    """
    Given an object id, this method overwrites the inner
    content of the post with `new_content`.

    This means that it won't change the frontmatter (eg tags, id, title)
    but it can change the file content.

    For example:

    If we have a dataobj like this:

    ```md
    ---
    id: 1
    title: Note
    ---

    # This is random
    ```

    Calling `update_item(1, "# This is specific")` will turn it into:


    ```md
    ---
    id: 1 # unchanged
    title: Note
    ---

    # This is specific
    ```
    """

    from archivy.models import DataObj
    filename = get_by_id(dataobj_id)
    dataobj = frontmatter.load(filename)
    dataobj.content = new_content
    md = frontmatter.dumps(dataobj)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)

    converted_dataobj = DataObj.from_md(md)
    converted_dataobj.fullpath = str(filename.relative_to(current_app.config["USER_DIR"]))
    converted_dataobj.index()
    load_hooks().on_edit(converted_dataobj)


def get_dirs():
    """Gets all dir names where dataobjs are stored"""
    # join glob matchers
    dirnames = [str(dir_path.relative_to(get_data_dir())) for dir_path
                in get_data_dir().rglob("*") if dir_path.is_dir()]

    # append name for root dir
    dirnames.append("not classified")
    return dirnames


def create_dir(name):
    """Create dir of given name"""
    root_dir = get_data_dir()
    new_path = root_dir / name.strip("/")
    if is_relative_to(new_path, root_dir):
        new_path.mkdir(parents=True, exist_ok=True)
        return str(new_path.relative_to(root_dir))
    return False


def delete_dir(name):
    """Deletes dir of given name"""
    root_dir = get_data_dir()
    target_dir = root_dir / name
    if not is_relative_to(target_dir, root_dir) or target_dir == root_dir:
        return False
    try:
        rmtree(target_dir)
        return True
    except FileNotFoundError:
        return False


def format_file(path: str):
    """
    Converts normal md of file at `path` to formatted archivy markdown file, with yaml front matter
    and a filename of format "{id}-{old_filename}.md"
    """

    from archivy.models import DataObj
    data_dir = get_data_dir()
    path = Path(path)
    if not path.exists():
        return

    if path.is_dir():
        for filename in path.iterdir():
            format_file(filename)

    else:
        new_file = path.open()
        file_contents = new_file.read()
        new_file.close()
        try:
            # get relative path of object in `data` dir
            datapath = path.parent.resolve().relative_to(data_dir)
        except ValueError:
            datapath = Path()

        note_dataobj = {
                "title": path.name.replace(".md", ""),
                "content": file_contents,
                "type": "note",
                "path": str(datapath)
            }

        dataobj = DataObj(**note_dataobj)
        dataobj.insert()

        path.unlink()
        current_app.logger.info(
                f"Formatted and moved {str(datapath / path.name)} to {dataobj.fullpath}")


def unformat_file(path: str, out_dir: str):
    """
    Converts normal md of file at `path` to formatted archivy markdown file, with yaml front matter
    and a filename of format "{id}-{old_filename}.md"
    """

    data_dir = get_data_dir()
    path = Path(path)
    out_dir = Path(out_dir)
    if not path.exists() and out_dir.exists() and out_dir.is_dir():
        return

    if path.is_dir():
        path.mkdir(exist_ok=True)
        for filename in path.iterdir():
            unformat_file(filename, str(out_dir))

    else:
        dataobj = frontmatter.load(str(path))

        try:
            # get relative path of object in `data` dir
            datapath = path.parent.resolve().relative_to(data_dir)
        except ValueError:
            datapath = Path()

        # create subdir if doesn't exist
        (out_dir / datapath).mkdir(exist_ok=True)
        new_path = out_dir / datapath / f"{dataobj.metadata['title']}.md"
        with new_path.open("w") as f:
            f.write(dataobj.content)

        current_app.logger.info(f"Unformatted and moved {str(path)} to {str(new_path.resolve())}")
        path.unlink()


def open_file(path):
    """Cross platform way of opening file on user's computer"""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
