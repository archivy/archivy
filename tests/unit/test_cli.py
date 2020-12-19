import os
from tempfile import mkdtemp

from tinydb import Query

from archivy.cli import cli
from archivy.helpers import get_db
from archivy.models import DataObj
from archivy.data import get_items, create_dir, get_data_dir


def test_initialization(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    try:
        # conf shouldn't exist
        open(conf_path)
        assert False
    except FileNotFoundError:
        pass
    old_data_dir = test_app.config["USER_DIR"]
    
    with cli_runner.isolated_filesystem():
        # create user, localhost, and don't use ES
        res = cli_runner.invoke(click_cli, ["init"], input="\nn\ny\nusername\npassword\npassword\n\n")
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
    assert "HOST: 127.0.0.1"
    # check ES config not saved
    assert "ELASTICSEARCH" not in conf

    # check initialization in random directory
    # has resulted in change of user dir
    assert old_data_dir != test_app.config["USER_DIR"]



def test_initialization_with_es(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    old_data_dir = test_app.config["USER_DIR"]
    
    with cli_runner.isolated_filesystem():
        # use ES, localhost and don't create user
        res = cli_runner.invoke(click_cli, ["init"], input="\ny\nn\n\n")

    assert "Config successfully created" in res.output
    conf = open(conf_path).read()

    # assert ES Config is saved
    assert "SEARCH_CONF" in conf
    assert "enabled: 1" in conf
    assert "url: http://localhost:9200" in conf

    # check initialization in random directory
    # has resulted in change of user dir
    assert old_data_dir != test_app.config["USER_DIR"]


def test_initialization_in_diff_than_curr_dir(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    data_dir = mkdtemp()
    
    with cli_runner.isolated_filesystem():
        # input data dir - localhost - don't use ES and don't create user
        res = cli_runner.invoke(cli, ["init"], input=f"{data_dir}\nn\nn\n\n")

    assert "Config successfully created" in res.output
    conf = open(conf_path).read()

    assert f"USER_DIR: {data_dir}" in conf


    # check initialization in random directory
    # has resulted in change of user dir
    assert data_dir == test_app.config["USER_DIR"]

    # verify dataobj creation works
    assert DataObj(type="note", title="Test note").insert()
    assert len(get_items(structured=False)) == 1


def test_initialization_custom_host(test_app, cli_runner, click_cli):
    conf_path = os.path.join(test_app.config["USER_DIR"], "config.yml")
    try:
        # conf shouldn't exist
        open(conf_path)
        assert False
    except FileNotFoundError:
        pass
    
    with cli_runner.isolated_filesystem():
        # create user, localhost, and don't use ES
        res = cli_runner.invoke(click_cli, ["init"],
                input="\nn\nn\n0.0.0.0")
        assert "Host" in res.output
        assert "Config successfully created" in res.output

    conf = open(conf_path).read()

    # assert defaults are saved
    print(res.output)
    assert f"HOST: 0.0.0.0" in conf


def test_create_admin(test_app, cli_runner, click_cli):
    db = get_db()
    nb_users = len(db.search(Query().type == "user"))
    cli_runner.invoke(click_cli,
                       ["create-admin", "__username__"],
                       input="password\npassword")

    # need to reconnect to db because it has been modified by different processes
    # so the connection needs to be updated for new changes
    db = get_db(force_reconnect=True)
    assert nb_users + 1 == len(db.search(Query().type == "user"))
    assert len(db.search(Query().type == "user" and Query().username == "__username__"))

def test_create_admin_small_password_fails(test_app, cli_runner, click_cli):
    cli_runner.invoke(click_cli,
                       ["create-admin", "__username__"],
                       input="short\nshort")
    db = get_db()
    assert not len(db.search(Query().type == "user" and Query().username == "__username__"))


def test_format_multiple_md_file(test_app, cli_runner, click_cli):
    with cli_runner.isolated_filesystem():
        files = ["test-note-1.md", "test-note-2.md"]
        for filename in files:
            with open(filename, "w") as f:
                f.write("Unformatted Test Content")

        res = cli_runner.invoke(cli, ["format"] + files)

        for filename in files:
            assert f"Formatted and moved {filename}" in res.output

def test_format_entire_directory(test_app, cli_runner, click_cli):
    with cli_runner.isolated_filesystem():
        files = ["unformatted/test-note-1.md", "unformatted/test-note-2.md", "unformatted/nested/test-note-3.md"]
        os.mkdir("data")
        os.mkdir("data/unformatted")
        os.mkdir("data/unformatted/nested")

        for filename in files:
            with open("data/" + filename, "w") as f:
                f.write("Unformatted Test Content")

        # set user_dir to current dir by configuring
        res = cli_runner.invoke(cli, ["init"], input="\nn\nn\n\n\n")

        # format directory
        res = cli_runner.invoke(cli, ["format", "data/unformatted/"])

        for filename in files:
            # assert directory files got moved correctly
            assert f"Formatted and moved {filename}" in res.output
        assert(os.path.abspath("") + "/data/unformatted") in res.output


def test_unformat_multiple_md_file(test_app, cli_runner, click_cli, bookmark_fixture, note_fixture):
    out_dir = mkdtemp()
    create_dir("")
    res = cli_runner.invoke(cli, ["unformat", str(bookmark_fixture.fullpath), str(note_fixture.fullpath), out_dir])
    assert f"Unformatted and moved {bookmark_fixture.fullpath} to {out_dir}/{bookmark_fixture.title}" in res.output
    assert f"Unformatted and moved {note_fixture.fullpath} to {out_dir}/{note_fixture.title}" in res.output


def test_unformat_directory(test_app, cli_runner, click_cli, bookmark_fixture, note_fixture):
    out_dir = mkdtemp()

    # create directory to store archivy note
    note_dir = "note-dir"
    create_dir(note_dir)
    nested_note = DataObj(type="note", title="Nested note", path=note_dir)
    nested_note.insert()

    # unformat directory
    res = cli_runner.invoke(cli, ["unformat", os.path.join(get_data_dir(), note_dir), out_dir])
    assert f"Unformatted and moved {nested_note.fullpath} to {out_dir}/{note_dir}/{nested_note.title}" in res.output
