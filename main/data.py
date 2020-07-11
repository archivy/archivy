import os
from main import app
import frontmatter
import glob
import re

dirname = "data/"

# method from django to sanitize filename
def valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def get_items(**kwargs):
    bookmarks = []
    for filename in glob.glob(dirname + "*.md"):
        data = frontmatter.load(filename)
        if 'type' in kwargs:
            for datatype in kwargs['type']:
                if (data['type'] == datatype):
                    bookmarks.append(data)
                    break
        else:
            bookmarks.append(data)
    return bookmarks


def create(contents, title):
    with open(dirname + valid_filename(title) + ".md", 'w') as f:
        f.write(contents)


def get_item(id):
    file = glob.glob(f"{dirname}{id}-*.md")[0]
    return frontmatter.load(file)


def delete_item(id):
    file = glob.glob(f"{dirname}{id}-*.md")[0]
    os.remove(file)
