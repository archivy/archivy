import responses
from flask import Flask
from flask.testing import FlaskClient


def test_bookmark_not_found(test_app, client: FlaskClient):
    response: Flask.response_class = client.get('/api/bookmarks/1')
    assert response.status_code == 404


def test_get_bookmark(test_app, client: FlaskClient, bookmark_fixture):
    response: Flask.response_class = client.get('/api/bookmarks/1')
    assert response.status_code == 200
    assert response.json['title'] == 'Example'
    assert response.json['bookmark_id'] == 1
    assert response.json['content'].startswith('Lorem ipsum')


def test_create_bookmark(test_app, client: FlaskClient, mocked_responses):
    mocked_responses.add(responses.GET, 'http://example.org', body="Example\n")
    response: Flask.response_class = client.post('/api/bookmarks', json={
        'url': 'http://example.org',
        'desc': 'Example web page',
        'tags': ['test'],
        'path': '',
    })
    assert response.status_code == 200

    response: Flask.response_class = client.get('/api/bookmarks/1')
    assert response.status_code == 200
    assert response.json['title'] == 'http://example.org'
    assert response.json['bookmark_id'] == 1
    assert response.json['content'] == 'Example'


def test_delete_bookmark_not_found(test_app, client: FlaskClient):
    response: Flask.response_class = client.delete('/api/bookmarks/1')
    assert response.status_code == 404


def test_delete_bookmark(test_app, client: FlaskClient, bookmark_fixture):
    response: Flask.response_class = client.delete('/api/bookmarks/1')
    assert response.status_code == 204


def test_get_bookmarks_with_empty_db(test_app, client: FlaskClient):
    response: Flask.response_class = client.get('/api/bookmarks')
    assert response.status_code == 200
    assert response.json == {'bookmarks': []}


def test_get_bookmarks(test_app, client: FlaskClient, bookmark_fixture):
    response: Flask.response_class = client.get('/api/bookmarks')
    assert response.status_code == 200
    assert isinstance(response.json['bookmarks'], list)
    bookmark = response.json['bookmarks'][0]
    assert bookmark['title'] == 'Example'
    assert bookmark['bookmark_id'] == 1
    assert bookmark['content'].startswith('Lorem ipsum')


def test_put_bookmark(test_app, client: FlaskClient):
    response: Flask.response_class = client.put('/api/bookmarks/1')
    assert response.status_code == 501
