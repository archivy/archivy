import os
import shutil
import tempfile

import pytest
import responses

from archivy import app
from archivy.extensions import get_db
from archivy.models import DataObj


@pytest.fixture
def test_app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    app_dir = tempfile.mkdtemp()
    app.config['APP_PATH'] = app_dir
    data_dir = os.path.join(app_dir, "data")
    os.mkdir(data_dir)

    app.config['TESTING'] = True

    # create the database and load test data
    with app.app_context():
        _ = get_db()

    yield app

    # close and remove the temporary database
    shutil.rmtree(app_dir)


@pytest.fixture
def client(test_app):
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        rsps.assert_all_requests_are_fired = True
        yield rsps


@pytest.fixture()
def note_fixture(test_app):
    datapoints = {"type": "note", "title": "Test Note", "desc": "A note to test model functionality", "tags": ["testing", "archivy"], "path": ""}

    with test_app.app_context():
        note = DataObj(**datapoints)
        note.insert()
    return note
