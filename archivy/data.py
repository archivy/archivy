import platform
import subprocess
import os
from pathlib import Path
import shutil

import frontmatter
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from archivy.search import remove_from_index


# FIXME: ugly hack to make sure the app path is evaluated at the right time
def get_data_dir():
    """Returns the directory where dataobjs are stored"""
    return Path(current_app.config["USER_DIR"]) / "data"


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


def build_dir_tree(path, query_dir, load_content=True):
    """
    Builds a structured tree of directories and data objects.

    - **path**: name of the directory relative to the root directory.
    - **query_dir**: absolute path of the directory we're building the tree of.
    - **load_content**: internal option to not save post contents in memory
        if they're not going to be accessed.
    """
    datacont = Directory(path or "root")
    for filepath in query_dir.rglob("*"):
        current_path = filepath.relative_to(query_dir)
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
            if not load_content:
                data.content = ""
            current_dir.child_files.append(data)
    return datacont


def get_items(
    collections=[], path="", structured=True, json_format=False, load_content=True
):
    """
    Gets all dataobjs.

    Parameters:

    - **collections** - filter dataobj by type, eg. bookmark / note
    - **path** - filter by path
    - **structured: if set to True, will return a Directory object, otherwise
      data will just be returned as a list of dataobjs
    - **json_format**: boolean value used internally to pre-process dataobjs
      to send back a json response.
    - **load_content**: internal value to disregard post content and not save them in memory if they won't be accessed.
    """
    data_dir = get_data_dir()
    query_dir = data_dir / path
    if not is_relative_to(query_dir, data_dir) or not query_dir.exists():
        raise FileNotFoundError
    if structured:
        return build_dir_tree(path, query_dir)
    else:
        datacont = []
        for filepath in query_dir.rglob("*.md"):
            data = frontmatter.load(filepath)
            if not load_content:
                data.content = ""
            data["fullpath"] = str(filepath.parent.relative_to(query_dir))
            if len(collections) == 0 or any(
                [collection == data["type"] for collection in collections]
            ):
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
    filename = secure_filename(title)
    data_dir = get_data_dir()
    max_filename_length = 255
    if len(filename + ".md") > max_filename_length:
        filename = filename[0 : max_filename_length - 3]
    path_to_md_file = data_dir / path.strip("/") / f"{filename}.md"
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
        # replace . for root items to ''
        if data["dir"] == ".":
            data["dir"] = ""
        return data
    return None


def move_item(dataobj_id, new_path):
    """Move dataobj of given id to new_path"""
    file = get_by_id(dataobj_id)
    data_dir = get_data_dir()
    out_dir = (data_dir / new_path).resolve()
    if not file:
        raise FileNotFoundError
    if (out_dir / file.parts[-1]).exists():
        raise FileExistsError
    elif is_relative_to(out_dir, data_dir) and out_dir.exists():  # check file isn't
        return shutil.move(str(file), f"{get_data_dir()}/{new_path}/")
    return False


def rename_folder(old_path, new_name):
    data_dir = get_data_dir()
    curr_dir = (data_dir / old_path).resolve()
    suggested_renaming = (curr_dir.parent / new_name).resolve()
    if (
        not is_relative_to(suggested_renaming, data_dir)
        or curr_dir == data_dir
        or suggested_renaming == data_dir
        or not is_relative_to(curr_dir, data_dir)
        or not suggested_renaming.parent.is_dir()
    ):
        return False  # invalid inputs
    if not curr_dir.is_dir():
        raise FileNotFoundError
    if suggested_renaming.exists():
        raise FileExistsError
    curr_dir.rename(suggested_renaming)
    return str(suggested_renaming.relative_to(data_dir))


def delete_item(dataobj_id):
    """Delete dataobj of given id"""
    file = get_by_id(dataobj_id)
    remove_from_index(dataobj_id)
    if file:
        Path(file).unlink()


def update_item_md(dataobj_id, new_content):
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
    converted_dataobj.fullpath = str(
        filename.relative_to(current_app.config["USER_DIR"])
    )
    converted_dataobj.index()
    current_app.config["HOOKS"].on_edit(converted_dataobj)


def update_item_frontmatter(dataobj_id, new_frontmatter):
    """
    Given an object id, this method overwrites the front matter
    of the post with `new_frontmatter`.

    ---
    date: Str
    id: Str
    path: Str
    tags: List[Str]
    title: Str
    type: note/bookmark
    ---
    """

    from archivy.models import DataObj

    filename = get_by_id(dataobj_id)
    dataobj = frontmatter.load(filename)
    for key in list(new_frontmatter):
        dataobj[key] = new_frontmatter[key]
    md = frontmatter.dumps(dataobj)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)

    converted_dataobj = DataObj.from_md(md)
    converted_dataobj.fullpath = str(
        filename.relative_to(current_app.config["USER_DIR"])
    )
    converted_dataobj.index()
    current_app.config["HOOKS"].on_edit(converted_dataobj)


def get_dirs():
    """Gets all dir names where dataobjs are stored"""
    # join glob matchers
    dirnames = [
        str(dir_path.relative_to(get_data_dir()))
        for dir_path in get_data_dir().rglob("*")
        if dir_path.is_dir()
    ]

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
        shutil.rmtree(target_dir)
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
        new_file = path.open("r", encoding="utf-8")
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
            "path": str(datapath),
        }

        dataobj = DataObj(**note_dataobj)
        dataobj.insert()

        path.unlink()
        current_app.logger.info(
            f"Formatted and moved {str(datapath / path.name)} to {dataobj.fullpath}"
        )


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

        current_app.logger.info(
            f"Unformatted and moved {str(path)} to {str(new_path.resolve())}"
        )
        path.unlink()


def open_file(path):
    """Cross platform way of opening file on user's computer"""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def valid_image_filename(filename):
    ALLOWED_EXTENSIONS = ["jpg", "png", "gif", "jpeg"]
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


def save_image(image: FileStorage):
    """
    Saves image to USER_DATA_DIR

    Returns: filename where image has been saved.
    """
    base_path = Path(current_app.config["USER_DIR"]) / "images"
    fileparts = image.filename.rsplit(".", 1)
    sanitized_filename = secure_filename(fileparts[0])
    dest_path = base_path / f"{sanitized_filename}.{fileparts[1]}"
    i = 1
    while dest_path.exists():
        dest_path = base_path / f"{sanitized_filename}-{i}.{fileparts[1]}"
        i += 1
    image.save(str(dest_path))
    return dest_path.parts[-1]


def image_exists(filename: str):
    sanitized = secure_filename(filename)
    images_dir = Path(current_app.config["USER_DIR"]) / "images"
    image_path = images_dir / sanitized
    if image_path.exists() and is_relative_to(image_path, images_dir):
        return str(image_path)
    return 0
