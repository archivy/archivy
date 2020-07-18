import os
from main import app
import frontmatter
import glob
import re
from pathlib import Path
from shutil import rmtree

dirname = "data/"

class Directory:

    def __init__(self, name):
        self.name = name
        self.child_files = []
        self.child_dirs = {}

# method from django to sanitize filename
def valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def get_items(collections=[], path="", structured=True):
    datacont = None
    if structured:
        # for structured datacont
        datacont = Directory("root")
    else:
        # unstructured
        datacont = []
    if structured:
        for filename in glob.glob(dirname + path + "**/*", recursive=True):
            paths = filename.split("/")
            data = frontmatter.load(filename) if filename.endswith(".md") else None
            current_dir = datacont
            for segment in paths[1:]:
                if segment.endswith(".md"):
                    current_dir.child_files.append(data)
                else:
                    if not segment in current_dir.child_dirs:
                        current_dir.child_dirs[segment] = Directory(segment)
                    current_dir = current_dir.child_dirs[segment]
    else:
        for filename in glob.glob(dirname + path + "**/*.md", recursive=True):
            data = frontmatter.load(filename)
            if collections == [] or any([collection == data['collection'] for collection in collections]):
                datacont.append(data)

    return datacont

def create(contents, title, path=''):
    with open(dirname + path + "/" + valid_filename(title) + ".md", 'w') as f:
        f.write(contents)


def get_item(id):
    file = glob.glob(f"{dirname}**/{id}-*.md", recursive=True)[0]
    return frontmatter.load(file)


def delete_item(id):
    file = glob.glob(f"{dirname}**/{id}-*.md", recursive=True)[0]
    os.remove(file)

def get_dirs():
    dirnames = glob.glob(dirname + "**/*", recursive=True)
    dirnames = ["/".join(name.split("/")[1:]) for name in dirnames if not name.endswith(".md")]
    dirnames.append("not classified")
    return dirnames

def create_dir(name):
    sanitized_name = "/".join([valid_filename(pathname) for pathname in name.split("/")])
    Path(dirname + sanitized_name).mkdir(parents=True, exist_ok=True) 

def delete_dir(name):
    try:
        rmtree(dirname + name)
        return True
    except FileNotFoundError:
        return False
