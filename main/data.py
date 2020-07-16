import os
from main import app
import frontmatter
import glob
import re
from pathlib import Path

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
    for filename in glob.glob(dirname + path + "**/*.md", recursive=True):
        data = frontmatter.load(filename)
        if collections == [] or any([collection == data['collection'] for collection in collections]):
            paths = filename.split("/")
            if structured:
                if len(paths) == 1:
                    datacont.child_files.append(data)
                else:
                    current_dir = datacont
                    for dir_name in paths[1:-1]:
                        if not dir_name in current_dir.child_dirs:
                           current_dir.child_dirs[dir_name] = Directory(dir_name)
                        current_dir = current_dir.child_dirs[dir_name]
                    current_dir.child_files.append(data)
            else: datacont.append(data)
    return datacont

def create(contents, title, path=''):
    current_dir = dirname
    for path in path.split("/"):
        Path(current_dir + path).mkdir(parents=True, exist_ok=True)
        current_dir += path + "/"
    with open(dirname + path + "/" + valid_filename(title) + ".md", 'w') as f:
        f.write(contents)


def get_item(id):
    file = glob.glob(f"{dirname}**/{id}-*.md", recursive=True)[0]
    return frontmatter.load(file)


def delete_item(id):
    file = glob.glob(f"{dirname}**/{id}-*.md", recursive=True)[0]
    os.remove(file)
