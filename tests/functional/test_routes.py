import os
import re

from flask.testing import FlaskClient
from flask import request
from flask_login import current_user
from responses import RequestsMock, GET
from werkzeug.security import generate_password_hash

from archivy.helpers import get_max_id, get_db
from archivy.data import get_dirs, create_dir, get_items, get_item


def test_get_index(test_app, client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200


def test_get_custom_css(test_app, client: FlaskClient):
    test_app.config["THEME_CONF"]["use_custom_css"] = True
    css_file = "custom.css"
    css_contents = """
        body {
            color: red
        }
    """

    os.mkdir(f"{test_app.config['USER_DIR']}/css/")
    with open(f"{test_app.config['USER_DIR']}/css/{css_file}", "w") as f:
        f.write(css_contents)
    test_app.config["THEME_CONF"]["custom_css_file"] = css_file
    resp = client.get("/static/custom.css")
    assert css_contents.encode("utf-8") in resp.data
    test_app.config["THEME_CONF"]["use_custom_css"] = False


def test_get_new_bookmark(test_app, client: FlaskClient):
    response = client.get("/bookmarks/new")
    assert response.status_code == 200


def test_post_new_bookmark_missing_fields(test_app, client: FlaskClient):
    response = client.post("/bookmarks/new", data={"submit": True})
    assert response.status_code == 200
    assert b"This field is required" in response.data


def test_get_new_note(test_app, client: FlaskClient):
    response = client.get("/notes/new")
    assert response.status_code == 200


def test_get_dataobj_not_found(test_app, client: FlaskClient):
    response = client.get("/dataobj/1")
    assert response.status_code == 302


def test_get_dataobj(test_app, client: FlaskClient, note_fixture):
    response = client.get("/dataobj/1")
    assert response.status_code == 200


def test_get_delete_dataobj_not_found(test_app, client: FlaskClient):
    response = client.get("/dataobj/delete/1")
    assert response.status_code == 302


def test_get_delete_dataobj(test_app, client: FlaskClient, note_fixture):
    response = client.get("/dataobj/delete/1")
    assert response.status_code == 302


def test_create_new_bookmark(
    test_app, client: FlaskClient, mocked_responses: RequestsMock
):
    mocked_responses.add(
        GET,
        "https://example.com/",
        body="""<html>
        <head><title>Random</title></head><body><p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit
        </p></body></html>
    """,
    )

    bookmark_data = {
        "url": "https://example.com",
        "tags": "testing,bookmark",
        "path": "",
        "submit": "true",
    }

    resp = client.post("/bookmarks/new", data=bookmark_data)
    assert resp.status_code == 302
    assert not b"invalid" in resp.data

    resp = client.post("/bookmarks/new", data=bookmark_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b'<span class="post-tag">bookmark</span>' in resp.data
    assert b'<span class="post-tag">testing</span>' in resp.data
    assert b"https://example.com" in resp.data
    assert b"Random" in resp.data


def test_creating_bookmark_without_passing_path_saves_to_default_dir(
    test_app, client, mocked_responses
):
    mocked_responses.add(GET, "http://example.org", body="Example\n")
    bookmarks_dir = "bookmarks"
    test_app.config["DEFAULT_BOOKMARKS_DIR"] = bookmarks_dir
    create_dir(bookmarks_dir)
    resp = client.post(
        "/bookmarks/new",
        data={
            "url": "http://example.org",
            "submit": "true",
        },
    )
    bookmark = get_items(structured=False)[0]
    assert (
        "bookmarks" in bookmark["path"]
    )  # verify it was saved to default bookmark dir


def test_create_note(test_app, client: FlaskClient):

    note_data = {
        "title": "Testing the create route",
        "tags": "testing,note",
        "path": "",
        "submit": "true",
    }

    resp = client.post("/notes/new", data=note_data)
    assert resp.status_code == 302
    assert not b"invalid" in resp.data

    resp = client.post("/notes/new", data=note_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b'<span class="post-tag">note</span>' in resp.data
    assert b'<span class="post-tag">testing</span>' in resp.data
    assert b"Testing the create route" in resp.data


def test_logging_in(test_app, client: FlaskClient):
    resp = client.post(
        "/login",
        data={"username": "halcyon", "password": "password"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert request.path == "/"
    assert current_user


def test_logging_in_with_invalid_creds(test_app, client: FlaskClient):
    resp = client.post(
        "/login",
        data={"username": "invalid", "password": "dasdasd"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert request.path == "/login"
    assert b"Invalid credentials" in resp.data


def test_edit_user(test_app, client: FlaskClient):
    """Tests editing a user's info, logging out and then logging in with new info."""

    new_user = "new_halcyon"
    new_pass = "password2"
    resp = client.post(
        "/user/edit",
        data={"username": new_user, "password": new_pass},
        follow_redirects=True,
    )

    assert request.path == "/"

    client.delete("/logout")

    resp = client.post(
        "/login",
        data={"username": new_user, "password": new_pass},
        follow_redirects=True,
    )
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

    resp = client.post(
        "/folders/create",
        data={"parent_dir": "", "new_dir": "testing"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert request.args.get("path") == "testing"
    assert "testing" in get_dirs()
    assert b"Folder successfully created" in resp.data


def test_creating_without_dirname_fails(test_app, client: FlaskClient):
    resp = client.post(
        "/folders/create", data={"parent_dir": ""}, follow_redirects=True
    )

    assert resp.status_code == 200
    assert request.path == "/"
    assert b"Could not create folder." in resp.data


def test_visiting_nonexistent_dir_fails(test_app, client: FlaskClient):
    resp = client.get("/?path=nonexistent_dir", follow_redirects=True)
    assert b"Directory does not exist." in resp.data


def test_deleting_dir(test_app, client: FlaskClient):
    create_dir("testing")
    assert "testing" in get_dirs()
    resp = client.post(
        "/folders/delete", data={"dir_name": "testing"}, follow_redirects=True
    )
    assert not "testing" in get_dirs()
    assert b"Folder successfully deleted." in resp.data


def test_deleting_nonexisting_folder_fails(test_app, client: FlaskClient):
    resp = client.post("/folders/delete", data={"dir_name": "testing"})
    assert resp.status_code == 404


def test_bookmarklet(test_app, client: FlaskClient):
    resp = client.get("/bookmarklet")
    assert resp.status_code == 200


def test_backlinks_are_saved(
    test_app, client: FlaskClient, note_fixture, bookmark_fixture
):
    test_app.config["SEARCH_CONF"]["enabled"] = 1
    test_app.config["SEARCH_CONF"]["engine"] = "ripgrep"

    resp = client.put(
        f"/api/dataobjs/{note_fixture.id}",
        json={
            "content": f"[[{bookmark_fixture.title}|{bookmark_fixture.id}]]"
        },
    )
    assert resp.status_code == 200

    resp = client.get(f"/dataobj/{bookmark_fixture.id}")
    assert b"Backlinks" in resp.data  # backlink was detected
    test_app.config["SEARCH_CONF"]["enabled"] = 0


def test_bookmark_with_long_title_gets_truncated(test_app, client, mocked_responses):

    long_title = "a" * 300
    # check that our mock title is indeed longer than the limit
    # and would cause an error, without our truncating
    assert os.pathconf("/", "PC_NAME_MAX") < len(long_title)
    mocked_responses.add(GET, "https://example.com", f"<title>{long_title}</title>")
    bookmark_data = {
        "url": "https://example.com",
        "submit": "true",
    }

    resp = client.post("/bookmarks/new", data=bookmark_data)
    assert resp.status_code == 200


def test_move_data(test_app, note_fixture, client):
    create_dir("random")

    resp = client.post(
        "/dataobj/move/1",
        data={"path": "random", "submit": "true"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Data successfully moved to random." in resp.data

    assert get_item(1)["dir"] == "random"


def test_invalid_inputs_fail_move_data(test_app, note_fixture, client):

    resp = client.post("/dataobj/move/1", follow_redirects=True)
    assert b"No path specified." in resp.data

    resp = client.post(
        "/dataobj/move/2", data={"path": "aaa", "submit": "true"}, follow_redirects=True
    )
    assert b"Data not found" in resp.data

    resp = client.post(
        "/dataobj/move/1", data={"path": "", "submit": "true"}, follow_redirects=True
    )
    assert b"Data already in target directory" in resp.data

    faulty_paths = ["../adarnad", "~/adasd", "ssss"]
    for p in faulty_paths:
        resp = client.post(
            "/dataobj/move/1", data={"path": p, "submit": "true"}, follow_redirects=True
        )
        assert b"Data could not be moved to " + bytes(p, "utf-8") in resp.data


def test_rename_dir(test_app, client):
    create_dir("random")

    resp = client.post(
        "/folders/rename",
        data={"current_path": "random", "new_name": "renamed_random"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Renamed successfully" in resp.data


def test_invalid_inputs_fail_renaming(test_app, client):
    create_dir("random")
    create_dir("random2")
    resp = client.post(
        "/folders/rename",
        data={"current_path": "inexisting", "new_name": "random3"},
        follow_redirects=True,
    )
    assert b"Directory not found" in resp.data

    resp = client.post(
        "/folders/rename",
        data={"current_path": "random", "new_name": "random2"},
        follow_redirects=True,
    )
    assert b"Target directory exists." in resp.data

    faulty_paths = ["../adarnad", "~/adasd", "/illegal_dir", "."]
    for p in faulty_paths:
        print(p)
        resp = client.post(
            "/folders/rename",
            data={"current_path": "random", "new_name": p},
            follow_redirects=True,
        )
        assert b"Invalid input" in resp.data


def test_get_config_page(test_app, client):
    resp = client.get("/config")
    assert resp.status_code == 200
    assert b"Edit Config" in resp.data


def test_post_updated_config(test_app, client):
    # use dark theme as random conf value to change
    dark_theme = test_app.config["THEME_CONF"]["use_theme_dark"]

    resp = client.post(
        "/config", data={"submit": True, "THEME_CONF-use_theme_dark": not dark_theme}
    )
    assert test_app.config["THEME_CONF"]["use_theme_dark"] == (not dark_theme)


def test_getting_all_tags(test_app, client, bookmark_fixture):
    # bookmark fixture has embedded tags
    resp = client.get("/tags")
    bookmark_tags = ["embedded-tag", "tag2"]
    assert resp.status_code == 200
    for tag in bookmark_tags:
        assert f"#{tag}" in str(resp.data)


def test_getting_matches_for_specific_tag(test_app, client, bookmark_fixture):
    resp = client.get("/tags/tag2")
    assert resp.status_code == 200
    assert bookmark_fixture.title in str(resp.data)
    assert str(bookmark_fixture.id) in str(resp.data)
