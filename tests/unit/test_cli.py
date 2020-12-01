import os
import tempfile

from tinydb import Query

from archivy.cli import cli
from archivy.helpers import get_db
from archivy.models import DataObj
from archivy.data import get_items


def test_initialization(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    try:
        # conf shouldn't exist
        open(conf_path)
        assert False
    except IOError:
        pass
    old_data_dir = test_app.config["USER_DIR"]
    
    with cli_runner.isolated_filesystem():
        # create user, and don't use ES
        res = cli_runner.invoke(cli, ["init"], input="y\nn\ny\nusername\npassword\npassword")
        assert "Config successfully created" in res.output

        # verify user was created
        assert len(get_db().search(Query().type == "user" and Query().username == "username"))

        # verify dataobj creation works
        assert DataObj(type="note", title="Test note").insert()
        assert len(get_items(structured=False)) == 1

    conf = open(conf_path).read()

    # assert defaults are saved
    assert "PANDOC_HIGHLIGHT_THEME: pygments" in conf
    assert f"USER_DIR: {test_app.config['USER_DIR']}" in conf
    # check ES config not saved
    assert "ELASTICSEARCH" not in conf

    # check initialization in random directory
    # has resulted in change of user dir
    assert old_data_dir != test_app.config["USER_DIR"]



def test_initialization_with_es(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    old_data_dir = test_app.config["USER_DIR"]
    
    with cli_runner.isolated_filesystem():
        # use ES and don't create user
        res = cli_runner.invoke(cli, ["init"], input="y\ny\nn")

    assert "Config successfully created" in res.output
    conf = open(conf_path).read()

    # assert ES Config is saved
    assert "ELASTICSEARCH" in conf
    assert "enabled: 1" in conf
    assert "url: http://localhost:9200" in conf

    # check initialization in random directory
    # has resulted in change of user dir
    assert old_data_dir != test_app.config["USER_DIR"]


def test_initialization_in_diff_than_curr_dir(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    data_dir = tempfile.mkdtemp()
    
    with cli_runner.isolated_filesystem():
        # input data dir - don't use ES and don't create user
        res = cli_runner.invoke(cli, ["init"], input=f"n\n{data_dir}\nn\nn")

    assert "Config successfully created" in res.output
    conf = open(conf_path).read()

    assert f"USER_DIR: {data_dir}" in conf


    # check initialization in random directory
    # has resulted in change of user dir
    assert data_dir == test_app.config["USER_DIR"]

    # verify dataobj creation works
    assert DataObj(type="note", title="Test note").insert()
    assert len(get_items(structured=False)) == 1



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
