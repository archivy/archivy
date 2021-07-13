from textwrap import dedent

import pytest
from tinydb import Query

from archivy.helpers import get_db, load_hooks, load_scraper
from archivy import data


@pytest.fixture()
def hooks_cli_runner(test_app, cli_runner, click_cli):
    """
    Saves hooks to user config directory for tests.

    All of the hooks except `before_dataobj_create` store some form of message in
    the db, whose existence is then checked in the tests.
    """
    hookfile = """\
        from archivy.config import BaseHooks
        from archivy.helpers import get_db

        class Hooks(BaseHooks):
            def on_edit(self, dataobj):
                get_db().insert({"type": "edit_message", "content": f"Changes made to content of {dataobj.title}."})
            def on_user_create(self, user):
                get_db().insert({"type": "user_creation_message", "content": f"New user {user.username} created."})
            def on_dataobj_create(self, dataobj):
                get_db().insert({"type": "dataobj_creation_message", "content": f"New dataobj on {dataobj.title} with tags: {dataobj.tags}"})
            def before_dataobj_create(self, dataobj):
                dataobj.content += "Dataobj made for test." """
    with cli_runner.isolated_filesystem():
        cli_runner.invoke(click_cli, ["init"], input="\nn\nn\n\n")
        with open("hooks.py", "w") as f:
            f.write(dedent(hookfile))
        with test_app.app_context():
            test_app.config["HOOKS"] = load_hooks()
        yield cli_runner


@pytest.fixture()
def custom_scraping_setup(test_app, cli_runner, click_cli):
    scraping_file = """\
            def test_pattern(data):
                data.title = "Overridden note"
                data.content = "this note was not processed by default archivy bookmarking, but a user-specified function"
                data.tags = ["test"]
            
            PATTERNS = {
                "https://example.com/": test_pattern,
                "https://example2.com/": ".nested"
            }"""

    with cli_runner.isolated_filesystem():
        cli_runner.invoke(click_cli, ["init"], input="\nn\nn\n\n")
        with open("scraping.py", "w") as f:
            f.write(dedent(scraping_file))
        with test_app.app_context():
            test_app.config["SCRAPING_PATTERNS"] = load_scraper()
        yield cli_runner


def test_dataobj_creation_hook(test_app, hooks_cli_runner, note_fixture):
    creation_message = get_db().search(Query().type == "dataobj_creation_message")[0]
    assert (
        creation_message["content"]
        == f"New dataobj on {note_fixture.title} with tags: {note_fixture.tags}"
    )


def test_before_dataobj_creation_hook(
    test_app, hooks_cli_runner, note_fixture, bookmark_fixture
):
    # check hook that added content at the end of body succeeded.
    message = "Dataobj made for test."
    assert message in note_fixture.content
    assert message in bookmark_fixture.content


def test_dataobj_edit_hook(test_app, hooks_cli_runner, note_fixture, client):
    client.put(
        f"/api/dataobjs/{note_fixture.id}", json={"content": "Updated note content"}
    )

    edit_message = get_db().search(Query().type == "edit_message")[0]
    assert (
        f"Changes made to content of {note_fixture.title}." == edit_message["content"]
    )


def test_user_creation_hook(test_app, hooks_cli_runner, user_fixture):
    creation_message = get_db().search(Query().type == "user_creation_message")[1]
    assert f"New user {user_fixture.username} created." == creation_message["content"]


def test_custom_scraping_patterns(
    custom_scraping_setup, test_app, bookmark_fixture, different_bookmark_fixture
):
    pattern = "example.com"
    assert pattern in bookmark_fixture.url
    assert bookmark_fixture.title == "Overridden note"
    assert bookmark_fixture.tags == ["test"]
    pattern = "example2.com"
    assert pattern in different_bookmark_fixture.url
    # check that the CSS selector was parsed and other parts of the document were not selected
    assert different_bookmark_fixture.content.startswith("aaa")
    test_app.config["SCRAPING_PATTERNS"] = {}
