from textwrap import dedent

import pytest
from tinydb import Query

from archivy.helpers import get_db
from archivy import data

@pytest.fixture()
def hooks_cli_runner(cli_runner, click_cli):
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
        yield cli_runner

def test_dataobj_creation_hook(test_app, hooks_cli_runner, note_fixture): 
    creation_message = get_db().search(Query().type == "dataobj_creation_message")[0]
    assert creation_message["content"] == f"New dataobj on {note_fixture.title} with tags: {note_fixture.tags}"

def test_before_dataobj_creation_hook(test_app, hooks_cli_runner, note_fixture, bookmark_fixture):
    # check hook that added content at the end of body succeeded.
    message = "Dataobj made for test."
    assert message in note_fixture.content
    assert message in bookmark_fixture.content


def test_dataobj_edit_hook(test_app, hooks_cli_runner, note_fixture, client):
    client.put(f"/api/dataobjs/{note_fixture.id}", json={"content": "Updated note content"})
    
    edit_message = get_db().search(Query().type == "edit_message")[0]
    assert f"Changes made to content of {note_fixture.title}." == edit_message["content"]


def test_user_creation_hook(test_app, hooks_cli_runner, user_fixture):
    creation_message = get_db().search(Query().type == "user_creation_message")[0]
    assert f"New user {user_fixture.username} created." == creation_message["content"]
