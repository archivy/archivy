import os
import shutil
import tempfile

import click
import pytest
import responses

from archivy import app, cli
from archivy.click_web import create_click_web_app, _flask_app
from archivy.helpers import get_db
from archivy.models import DataObj, User

_app = None

@pytest.fixture
def test_app():
    """Instantiate the app for each test with its own temporary data directory

    Each test using this fixture will use its own db.json and its own data
    directory, and then delete them.
    """
    # create a temporary file to isolate the database for each test
    global _app
    if _app is None:
        _app = create_click_web_app(cli, cli.cli, app) 
    app_dir = tempfile.mkdtemp()
    _app.config["INTERNAL_DIR"] = app_dir
    _app.config["USER_DIR"] = app_dir
    data_dir = os.path.join(app_dir, "data")
    os.mkdir(data_dir)

    _app.config["TESTING"] = True
    _app.config["WTF_CSRF_ENABLED"] = False
    # This setups a TinyDB instance, using the `app_dir` temporary
    # directory defined above
    # Required so that `flask.current_app` can be called in data.py and
    # models.py
    # See https://flask.palletsprojects.com/en/1.1.x/appcontext/ for more
    # information.
    with _app.app_context():
        _ = get_db()
        user = {
            "username": "halcyon",
            "password": "password"
        }

        User(**user).insert()
        yield _app

    # close and remove the temporary database
    shutil.rmtree(app_dir)


@pytest.fixture
def client(test_app):
    """ HTTP client for calling a test instance of the app"""
    with test_app.test_client() as client:
        client.post("/login", data={"username": "halcyon", "password": "password"})
        yield client


@pytest.fixture
def mocked_responses():
    """
    Setup mock responses using the `responses` python package.

    Using https://pypi.org/project/responses/, this fixture will mock out
    HTTP calls made by the requests library.

    For example,
    >>> mocked_responses.add(responses.GET, "http://example.org",
     json={'key': 'val'}
     )
    >>> r = requests.get("http://example.org")
    >>> print(r.json())
    {'key': 'val'}
    """
    with responses.RequestsMock() as rsps:
        # this ensure that all requests calls are mocked out
        rsps.assert_all_requests_are_fired = False
        yield rsps


@pytest.fixture
def note_fixture(test_app):
    note_dict = {
        "type": "note", "title": "Test Note",
        "tags": ["testing", "archivy"], "path": ""
    }

    with test_app.app_context():
        note = DataObj(**note_dict)
        note.insert()
    return note


@pytest.fixture
def bookmark_fixture(test_app, mocked_responses):
    mocked_responses.add(responses.GET, "https://example.com/", body="""<html>
        <head><title>Example</title></head><body><p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit
        <script>console.log("this should be sanitized")</script>
        <img src="/images/image1.png">
        <a href="/testing-absolute-url">link</a>
        <a href"/empty-link"></a>
        </p></body></html>
    """)

    datapoints = {
        "type": "bookmark", "title": "Test Bookmark",
        "tags": ["testing", "archivy"], "path": "",
        "url": "https://example.com/"
    }

    with test_app.app_context():
        bookmark = DataObj(**datapoints)
        bookmark.process_bookmark_url()
        bookmark.insert()
    return bookmark


@pytest.fixture()
def user_fixture(test_app):
    user = {
        "username": "__username__",
        "password": "__password__"
    }

    user = User(**user)
    user.insert()
    return user


@pytest.fixture()
def pocket_fixture(test_app, mocked_responses):
    """Sets up pocket key and mocked responses for testing pocket sync

    When using this fixture, all calls to https://getpocket.com/v3/get will
    succeed and return a single article whose url is https://example.com.
    """
    with test_app.app_context():
        db = get_db()

    mocked_responses.add(
        responses.POST,
        "https://getpocket.com/v3/oauth/authorize",
        json={
            "access_token": "5678defg-5678-defg-5678-defg56",
            "username": "test_user"
        })

    # fake /get response from pocket API
    mocked_responses.add(responses.POST, "https://getpocket.com/v3/get", json={
        'status': 1, 'complete': 1, 'list': {
            '3088163616': {
                'given_url': 'https://example.com', 'status': '0',
                'resolved_url': 'https://example.com',
                'excerpt': 'Lorem ipsum', 'is_article': '1',
            },
        },
    })

    pocket_key = {
        "type": "pocket_key",
        "consumer_key": "1234-abcd1234abcd1234abcd1234",
        "code": "dcba4321-dcba-4321-dcba-4321dc",
    }
    db.insert(pocket_key)
    return pocket_key

@pytest.fixture()
def click_cli():
    yield cli.cli

@pytest.fixture()
def ctx(click_cli):
    with click.Context(click_cli, info_name=click_cli, parent=None) as ctx:
        yield ctx

@pytest.fixture()
def cli_runner():
    yield click.testing.CliRunner()
