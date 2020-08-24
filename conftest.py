import pytest

from archivy.models import DataObj

@pytest.fixture(scope="session")
def note_fixture():
    datapoints = {"type": "note", "title": "Test Note", "desc": "A note to test model functionality", "tags": ["testing", "archivy"], "path": ""}

    note = DataObj(**datapoints)
    note.insert()
    return note
