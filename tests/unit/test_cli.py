from tinydb import Query

from archivy.cli import cli
from archivy.helpers import get_db

def test_create_admin(test_app, cli_runner, click_cli):
    db = get_db()
    nb_users = len(db.search(Query().type == "user"))
    cli_runner.invoke(cli,
                       ["create-admin", "__username__"],
                       input="password\npassword")

    # need to reconnect to db because it has been modified by different processes
    # so the connection needs to be updated for new changes
    db = get_db(force_reconnect=True)
    assert nb_users + 1 == len(db.search(Query().type == "user"))
    assert len(db.search(Query().type == "user" and Query().username == "__username__"))

def test_create_admin_small_password_fails(test_app, cli_runner, click_cli):
    cli_runner.invoke(cli,
                       ["create-admin", "__username__"],
                       input="short\nshort")
    db = get_db()
    assert not len(db.search(Query().type == "user" and Query().username == "__username__"))
