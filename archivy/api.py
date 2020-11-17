from flask import Response, jsonify, request, Blueprint, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user
from tinydb import Query

from archivy import data
from archivy.search import query_index
from archivy.config import Config
from archivy.models import DataObj, User
from archivy.helpers import get_db


api_bp = Blueprint('api', __name__)


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Logs in the API client using
    [HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication).
    Pass in the username and password of your account.
    """
    db = get_db()
    user = db.search(Query().username == request.authorization["username"])
    if (user and
            check_password_hash(
                user[0]["hashed_password"],
                request.authorization["password"])):
        # user is verified so we can log him in from the db
        user = User.from_db(user[0])
        login_user(user, remember=True)
        return Response(status=200)
    return Response(status=401)


@api_bp.route("/bookmarks", methods=["POST"])
def create_bookmark():
    """
    Creates a new bookmark

    **Parameters:**

    All parameters are sent through the JSON body.
    - **url** (required)
    - **desc**
    - **tags**
    - **path**
    """
    json_data = request.get_json()
    bookmark = DataObj(
        url=json_data['url'],
        desc=json_data.get('desc'),
        tags=json_data.get('tags'),
        path=json_data.get("path", ""),
        type="bookmark",
    )
    bookmark.process_bookmark_url()
    bookmark_id = bookmark.insert()
    if bookmark_id:
        return jsonify(
            bookmark_id=bookmark_id,
        )
    return Response(status=400)


@api_bp.route("/notes", methods=["POST"])
def create_note():
    """
    Creates a new note.

    **Parameters:**

    All parameters are sent through the JSON body.
    - **title** (required)
    - **content** (required)
    - **desc**
    - **tags**
    - **path**
    """
    json_data = request.get_json()
    note = DataObj(
        title=json_data["title"],
        content=json_data["content"],
        desc=json_data.get("desc"),
        tags=json_data.get("tags"),
        path=json_data.get("path", ""),
        type="note"
    )

    note_id = note.insert()
    if note_id:
        return jsonify(note_id=note_id)
    return Response(status=400)


@api_bp.route("/dataobjs/<int:dataobj_id>")
def get_dataobj(dataobj_id):
    """Returns dataobj of given id"""
    dataobj = data.get_item(dataobj_id)

    return jsonify(
        dataobj_id=dataobj_id,
        title=dataobj["title"],
        content=dataobj.content,
        md_path=dataobj["fullpath"],
    ) if dataobj else Response(status=404)


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["PUT"])
def change_bookmark(bookmark_id):
    current_app.logger.debug(f'Attempting to delete bookmark <{bookmark_id}>')
    return Response(status=501)


@api_bp.route("/dataobjs/<int:dataobj_id>", methods=["DELETE"])
def delete_dataobj(dataobj_id):
    """Deletes object of given id"""
    if not data.get_item(dataobj_id):
        return Response(status=404)
    data.delete_item(dataobj_id)
    return Response(status=204)


@api_bp.route("/dataobjs", methods=["GET"])
def get_dataobjs():
    """Gets all dataobjs"""
    cur_dir = data.get_items(structured=False, json_format=True)
    return jsonify(cur_dir)


@api_bp.route("/dataobj/local_edit/<dataobj_id>", methods=["GET"])
def local_edit(dataobj_id):
    dataobj = data.get_item(dataobj_id)
    if dataobj:
        data.open_file(dataobj["fullpath"])
        return Response(status=200)
    return Response(status=404)


@api_bp.route("/folders/new", methods=["POST"])
def create_folder():
    """
    Creates new directory

    Parameter in JSON body:
    - **path** (required) - path of newdir
    """
    directory = request.json.get("path")
    try:
        sanitized_name = data.create_dir(directory)
    except FileExistsError:
        return "Directory already exists", 401
    return sanitized_name, 200


@api_bp.route("/folders/delete", methods=["DELETE"])
def delete_folder():
    """
    Deletes directory.

    Parameter in JSON body:
    - **path** of dir to delete
    """
    directory = request.json.get("path")
    if directory == "":
        return "Cannot delete root dir", 401
    if data.delete_dir(directory):
        return "Successfully deleted", 200
    return "Not found", 404


@api_bp.route("/search", methods=["GET"])
def search_elastic():
    """
    Searches the instance.

    Request URL Parameter:
    - **query**
    """
    query = request.args.get("query")
    search_results = query_index(Config.INDEX_NAME, query)
    return jsonify(search_results)
