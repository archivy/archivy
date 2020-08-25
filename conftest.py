import os
import shutil
import tempfile

import pytest
import responses

from archivy import app, config
from archivy.models import DataObj

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app_dir = tempfile.mkdtemp()
    app.config['APP_PATH'] = app_dir
    data_dir = os.path.join(app_dir, "data")
    os.mkdir(data_dir)

    with app.test_client() as client:
        yield client

    shutil.rmtree(app_dir)

@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture(scope="session")
def note_fixture():
    datapoints = {"type": "note", "title": "Test Note", "desc": "A note to test model functionality", "tags": ["testing", "archivy"], "path": ""}

    note = DataObj(**datapoints)
    note.insert()
    return note
