import re

from flask.testing import FlaskClient
from flask import request
from flask_login import current_user

from responses import RequestsMock, GET
from archivy.helpers import get_max_id, get_db

def test_plugin_index(test_app, client: FlaskClient):
    resp = client.get("/plugins")
    assert resp.status_code == 200
    assert b'Plugins' in resp.data

    # random number is one of the seeded plugins we added for testing
    assert b'random-number' in resp.data


def test_get_command_form(test_app, client: FlaskClient):
    cmd_path = "/cli/test-plugin/random-number"
    resp = client.get(cmd_path)
    
    command_input = b"2.0.argument.text.1.text.upper-bound"
    command_name = b"Random-Number"

    assert command_input in resp.data
    assert command_name in resp.data


def test_exec_random_command(test_app, client: FlaskClient):
    cmd_path = "/cli/test-plugin/random-number"
    upper_bound = 10
    cmd_data = {"2.0.argument.text.1.text.upper-bound": upper_bound}
    
    resp = client.post(cmd_path, data=cmd_data)
    
    assert resp.status_code == 200
    # check for random number <= 10 in response
    assert re.match("(0*(?:[1-9]?|10))", str(resp.data))

def test_exec_command_app_context(test_app, note_fixture, bookmark_fixture, client: FlaskClient):
    cmd_path = "/cli/test-plugin/get-random-dataobj-title"
    resp = client.post(cmd_path)

    assert resp.status_code == 200
    assert b"Test Note" or b"Example" in resp.data

