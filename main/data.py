import os
from main import app
import frontmatter

dirname = "data/"

def get_items(**kwargs):
    bookmarks = []
    for filename in os.listdir(dirname):
        data = frontmatter.load(dirname + filename)
        print(data['type'])
        if 'type' in kwargs:
            if (data['type'] == kwargs['type']):
                bookmarks.append(data)
        else:
            bookmarks.append(data)
    return bookmarks

def create(contents, title):
    with open(dirname + title + ".md", 'w') as f:
        f.write(contents)
