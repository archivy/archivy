import frontmatter
import pytest

from archivy.extensions import get_max_id

attributes = ["type", "title", "desc", "tags", "path", "id"]

def test_new_note(note_fixture):
    """
    Check that a new note is correctly saved into the filesystem
    with the right attributes and the right id.
    """
    max_id = get_max_id()
    assert note_fixture.id + 1 == max_id
    
    saved_file = frontmatter.load(note_fixture.fullpath)
    for attr in attributes:
        assert getattr(note_fixture, attr) == saved_file[attr]




