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
    """Instantiate the app for each test with its own temporary data directory

    Each test using this fixture will use its own db.json and its own data
    directory, and then delete them.
    """
    # create a temporary file to isolate the database for each test
    app_dir = tempfile.mkdtemp()
    app.config['APP_PATH'] = app_dir
    data_dir = os.path.join(app_dir, "data")
    os.mkdir(data_dir)

    app.config['TESTING'] = True

    # This setups a TinyDB instance, using the `app_dir` temporary
    # directory defined above
    # Required so that `flask.current_app` can be called in data.py and
    # models.py
    # See https://flask.palletsprojects.com/en/1.1.x/appcontext/ for more
    # information.
    with app.app_context():
        _ = get_db()

    yield app

    # close and remove the temporary database
    shutil.rmtree(app_dir)


@pytest.fixture
def client(test_app):
    """ HTTP client for calling a test instance of the app"""
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def mocked_responses():
    """Setup mock responses using the `responses` python package.

    Using https://pypi.org/project/responses/, this fixture will mock out
    HTTP calls made by the requests library.

    For example,
    >>> mocked_responses.add(responses.GET, "http://example.org", json={'key': 'val'})
    >>> r = requests.get("http://example.org")
    >>> print(r.json())
    {'key': 'val'}
    """
    with responses.RequestsMock() as rsps:
        # this ensure that all requests calls are mocked out
        rsps.assert_all_requests_are_fired = True
        yield rsps


@pytest.fixture(scope="session")
def note_fixture():
    datapoints = {"type": "note", "title": "Test Note", "desc": "A note to test model functionality", "tags": ["testing", "archivy"], "path": ""}

    note = DataObj(**datapoints)
    note.insert()
    return note
