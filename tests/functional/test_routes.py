from flask.testing import FlaskClient
from flask import request
from flask_login import current_user

from responses import RequestsMock, GET
from werkzeug.security import generate_password_hash
from archivy.helpers import get_max_id, get_db
from archivy.data import get_dirs, create_dir


def test_get_index(test_app, client: FlaskClient):
    response = client.get('/')
    assert response.status_code == 200


def test_get_new_bookmark(test_app, client: FlaskClient):
    response = client.get('/bookmarks/new')
    assert response.status_code == 200


def test_post_new_bookmark_missing_fields(test_app, client: FlaskClient):
    response = client.post('/bookmarks/new', data={
        'submit': True
    })
    assert response.status_code == 200
    assert b'This field is required' in response.data

def test_get_new_note(test_app, client: FlaskClient):
    response = client.get('/notes/new')
    assert response.status_code == 200


def test_get_dataobj_not_found(test_app, client: FlaskClient):
    response = client.get('/dataobj/1')
    assert response.status_code == 302


def test_get_dataobj(test_app, client: FlaskClient, note_fixture):
    response = client.get('/dataobj/1')
    assert response.status_code == 200


def test_get_delete_dataobj_not_found(test_app, client: FlaskClient):
    response = client.get('/dataobj/delete/1')
    assert response.status_code == 302


def test_get_delete_dataobj(test_app, client: FlaskClient, note_fixture):
    response = client.get('/dataobj/delete/1')
    assert response.status_code == 302

def test_create_new_bookmark(test_app, client: FlaskClient, mocked_responses: RequestsMock):
    mocked_responses.add(GET, "https://example.com/", body="""<html>
        <head><title>Random</title></head><body><p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit
        </p></body></html>
    """)

    bookmark_data = {
        "url": "https://example.com",
        "tags": "testing,bookmark",
        "path": "not classified",
        "submit": "true"
    }

    resp = client.post("/bookmarks/new", data=bookmark_data)
    assert resp.status_code == 302
    assert not b"invalid" in resp.data

    resp = client.post("/bookmarks/new", data=bookmark_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"testing, bookmark" in resp.data
    assert b"https://example.com" in resp.data
    assert b"Random" in resp.data
    
def test_create_note(test_app, client: FlaskClient):

    note_data = {
        "title": "Testing the create route",
        "tags": "testing,note",
        "path": "not classified",
        "submit": "true"
    }


    resp = client.post("/notes/new", data=note_data)
    assert resp.status_code == 302
    assert not b"invalid" in resp.data

    resp = client.post("/notes/new", data=note_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"testing, note" in resp.data
    assert b"Testing the create route" in resp.data

def test_logging_in(test_app, client: FlaskClient):
    resp = client.post("/login", data={"username": "halcyon", "password": "password"}, follow_redirects=True)
    assert resp.status_code == 200
    assert request.path == "/"
    assert current_user

def test_logging_in_with_invalid_creds(test_app, client: FlaskClient):
    resp = client.post("/login", data={"username": "invalid", "password": "dasdasd"}, follow_redirects=True)
    assert resp.status_code == 200
    assert request.path == "/login"
    assert b"Invalid credentials" in resp.data
    
def test_edit_user(test_app, client: FlaskClient):
    """Tests editing a user's info, logging out and then logging in with new info."""

    new_user = "new_halcyon"
    new_pass = "password2"
    resp = client.post("/user/edit",
                data={"username": new_user, "password": new_pass},
                follow_redirects=True)
    
    assert request.path == "/"

    client.delete("/logout")

    resp = client.post("/login",
                        data={"username": new_user, "password": new_pass},
                        follow_redirects=True)
    assert resp.status_code == 200
    assert request.path == "/"
    # check information has updated.

def test_logging_out(test_app, client: FlaskClient):
    """Tests logging out and then accessing restricted views"""

    client.delete("/logout")

    resp = client.get("/", follow_redirects=True)
    assert request.path == "/login"


def test_create_dir(test_app, client: FlaskClient):
    """Tests /folders/create endpoint"""

    resp = client.post("/folders/create",
                data={"parent_dir": "", "new_dir": "testing"},
                follow_redirects=True)

    assert resp.status_code == 200
    assert request.args.get("path") == "testing"
    assert "testing" in get_dirs()
    assert b"Folder successfully created" in resp.data

def test_creating_without_dirname_fails(test_app, client: FlaskClient):
    resp = client.post("/folders/create",
                data={"parent_dir": ""},
                follow_redirects=True)

    assert resp.status_code == 200
    assert request.path == "/"
    assert b"Could not create folder." in resp.data


def test_visiting_nonexistent_dir_fails(test_app, client: FlaskClient):
    resp = client.get("/?path=nonexistent_dir", follow_redirects=True)
    assert b"Directory does not exist." in resp.data


def test_deleting_dir(test_app, client: FlaskClient):
    create_dir("testing")
    assert "testing" in get_dirs()
    resp = client.post("/folders/delete", data={"dir_name": "testing"}, follow_redirects=True)
    assert not "testing" in get_dirs()
    assert b"Folder successfully deleted." in resp.data


def test_deleting_nonexisting_folder_fails(test_app, client: FlaskClient):
    resp = client.post("/folders/delete", data={"dir_name": "testing"})
    assert resp.status_code == 404


def test_bookmarklet(test_app, client: FlaskClient):
    resp = client.get("/bookmarklet")
    assert resp.status_code == 200
