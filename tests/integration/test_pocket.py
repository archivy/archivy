import responses
from flask import Flask

from archivy import data
from archivy.extensions import get_db


def test_parse_pocket(test_app, client, mocked_responses):
    """Test the /pocket endpoint by mocking out the external HTTP calls to the
    pocket API
    """
    with test_app.app_context():
        db = get_db()

    mocked_responses.add(responses.POST, "https://getpocket.com/v3/get", json={
        'status': 1, 'complete': 1, 'list': {
            '3088163616': {
                'given_url': 'https://example.com', 'status': '0',
                'resolved_url': 'https://example.com',
                'excerpt': 'Lorem ipsum', 'is_article': '1',
            },
        },
    })

    mocked_responses.add(responses.GET, "https://example.com/", body="""<html>
        <head><title>Example</title></head><body><p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit
        </p></body></html>
    """)

    mocked_responses.add(
        responses.POST,
        "https://getpocket.com/v3/oauth/authorize",
        json={
            "access_token": "5678defg-5678-defg-5678-defg56",
            "username": "test_user"
        })

    pocket_key = {
        "type": "pocket_key",
        "consumer_key": "1234-abcd1234abcd1234abcd1234",
        "code": "dcba4321-dcba-4321-dcba-4321dc",
    }
    db.insert(pocket_key)

    r: Flask.response_class = client.get('/parse_pocket?new=1')
    assert r.status_code == 302

    dataobjs = data.get_items()
    assert len(dataobjs.child_files) == 1
