import os
from main import app
import frontmatter
import glob
dirname = "data/"

# method from django to sanitize filename
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    # ...
    return value

def get_items(**kwargs):
    bookmarks = []
    for filename in glob.glob(dirname + "*.md"):
        data = frontmatter.load(filename)
        if 'type' in kwargs:
            if (data['type'] == kwargs['type']):
                bookmarks.append(data)
        else:
            bookmarks.append(data)
    return bookmarks


def create(contents, title):
    with open(dirname + slugify(title) + ".md", 'w') as f:
        f.write(contents)


def get_item(id):
    file = glob.glob(f"{dirname}{id}-*.md")[0]
    return frontmatter.load(file)


def delete_item(id):
    file = glob.glob(f"{dirname}{id}-*.md")[0]
    os.remove(file)
