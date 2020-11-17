from base64 import b64encode

import responses
from flask import Flask
from flask.testing import FlaskClient
from archivy.data import create_dir, get_items
from archivy.models import DataObj

def test_bookmark_not_found(test_app, client: FlaskClient):
    response: Flask.response_class = client.get("/api/dataobjs/1")
    assert response.status_code == 404


def test_get_dataobj(test_app, client: FlaskClient, bookmark_fixture):
    response: Flask.response_class = client.get("/api/dataobjs/1")
    assert response.status_code == 200
    assert response.json["title"] == "Example"
    assert response.json["dataobj_id"] == 1
    assert response.json["content"].startswith("Lorem ipsum")


def test_create_bookmark(test_app, client: FlaskClient, mocked_responses):
    mocked_responses.add(responses.GET, "http://example.org", body="Example\n")
    response: Flask.response_class = client.post("/api/bookmarks", json={
        "url": "http://example.org",
        "desc": "Example web page",
        "tags": ["test"],
        "path": "",
    })
    assert response.status_code == 200

    response: Flask.response_class = client.get("/api/dataobjs/1")
    assert response.status_code == 200
    assert response.json["title"] == "http://example.org"
    assert response.json["dataobj_id"] == 1
    assert response.json["content"] == "Example"

def test_create_note(test_app, client: FlaskClient, mocked_responses):
    mocked_responses.add(responses.GET, "http://example.org", body="Example\n")
    response: Flask.response_class = client.post("/api/notes", json={
        "title": "Test Note created with api",
        "content": "Example",
        "tags": ["test"],
        "path": "",
    })
    assert response.status_code == 200

    response: Flask.response_class = client.get("/api/dataobjs/1")
    assert response.status_code == 200
    assert response.json["title"] == "Test Note created with api"
    assert response.json["dataobj_id"] == 1
    assert response.json["content"] == "Example"


def test_delete_bookmark_not_found(test_app, client: FlaskClient):
    response: Flask.response_class = client.delete("/api/dataobjs/1")
    assert response.status_code == 404


def test_delete_bookmark(test_app, client: FlaskClient, bookmark_fixture):
    response: Flask.response_class = client.delete("/api/dataobjs/1")
    assert response.status_code == 204


def test_get_bookmarks_with_empty_db(test_app, client: FlaskClient):
    response: Flask.response_class = client.get("/api/dataobjs")
    assert response.status_code == 200
    assert response.json == []


def test_get_dataobjs(test_app, client: FlaskClient, bookmark_fixture):

    note_dict = {
        "type": "note", "title": "Nested Test Note",
        "desc": "A note to test nested paths",
        "tags": ["testing", "archivy"], "path": "t"
    }

    create_dir("t")
    note = DataObj(**note_dict)
    note.insert()
    response: Flask.response_class = client.get("/api/dataobjs")
    print(response.data)
    assert response.status_code == 200
    assert isinstance(response.json, list)
    # check it correctly gets nested note
    assert len(response.json) == 2

    bookmark = response.json[0]
    assert bookmark["metadata"]["title"] == "Example"
    assert bookmark["metadata"]["id"] == 1
    assert bookmark["content"].startswith("Lorem ipsum")


def test_put_bookmark(test_app, client: FlaskClient):
    response: Flask.response_class = client.put("/api/bookmarks/1")
    assert response.status_code == 501

def test_api_login(test_app, client: FlaskClient):
    # logout
    client.delete("/logout")
    # requires converting to base64 for http basic auth
    authorization = "Basic " + b64encode('halcyon:password'.encode('ascii')).decode('ascii')
    resp = client.post("/api/login", headers={"Authorization": authorization})
    
    assert resp.status_code == 200
    resp = client.get("/api/dataobjs")
    assert resp.status_code == 200

def test_unlogged_in_api_fails(test_app, client: FlaskClient):
    client.delete("/logout")
    resp = client.get("/api/dataobjs")
    assert resp.status_code == 302

