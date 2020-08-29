from flask.testing import FlaskClient


def test_get_index(test_app, client: FlaskClient):
    response = client.get('/')
    assert response.status_code == 200


def test_get_new_bookmark(test_app, client: FlaskClient):
    response = client.get('/bookmarks/new')
    assert response.status_code == 200


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
    response = client.get('/dataobj/1')
    assert response.status_code == 302


def test_get_delete_dataobj(test_app, client: FlaskClient, note_fixture):
    response = client.get('/dataobj/delete/1')
    assert response.status_code == 302
