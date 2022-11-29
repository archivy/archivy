from flask import Response, jsonify, request, Blueprint, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user
from tinydb import Query

from archivy import data, tags
from archivy.search import search
from archivy.models import DataObj, User
from archivy.helpers import get_db


api_bp = Blueprint("api", __name__)


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Logs in the API client using
    [HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication).
    Pass in the username and password of your account.
    """
    db = get_db()
    user = db.search(Query().username == request.authorization["username"])
    if user and check_password_hash(
        user[0]["hashed_password"], request.authorization["password"]
    ):
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
    - **tags**
    - **path**
    """
    json_data = request.get_json()
    bookmark = DataObj(
        url=json_data["url"],
        tags=json_data.get("tags", []),
        path=json_data.get("path", current_app.config["DEFAULT_BOOKMARKS_DIR"]),
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
    - **tags**
    - **path**
    """
    json_data = request.get_json()
    note = DataObj(
        title=json_data["title"],
        content=json_data["content"],
        path=json_data.get("path", ""),
        tags=json_data.get("tags", []),
        type="note",
    )

    note_id = note.insert()
    if note_id:
        return jsonify(note_id=note_id)
    return Response(status=400)


@api_bp.route("/dataobjs/<int:dataobj_id>")
def get_dataobj(dataobj_id):
    """Returns dataobj of given id"""
    dataobj = data.get_item(dataobj_id)

    return (
        jsonify(
            dataobj_id=dataobj_id,
            title=dataobj["title"],
            content=dataobj.content,
            md_path=dataobj["fullpath"],
        )
        if dataobj
        else Response(status=404)
    )


@api_bp.route("/dataobjs/<int:dataobj_id>", methods=["DELETE"])
def delete_dataobj(dataobj_id):
    """Deletes object of given id"""
    if not data.get_item(dataobj_id):
        return Response(status=404)
    data.delete_item(dataobj_id)
    return Response(status=204)


@api_bp.route("/dataobjs/<int:dataobj_id>", methods=["PUT"])
def update_dataobj(dataobj_id):
    """
    Updates object of given id.

    Paramter in JSON body:

    - **content**: markdown text of new dataobj.
    """
    if request.json.get("content"):
        try:
            data.update_item_md(dataobj_id, request.json.get("content"))
            return Response(status=200)
        except BaseException:
            return Response(status=404)
    return Response("Must provide content parameter", status=401)


@api_bp.route("/dataobjs/frontmatter/<int:dataobj_id>", methods=["PUT"])
def update_dataobj_frontmatter(dataobj_id):
    """
    Updates frontmatter of object of given id.

    Paramter in JSON body:

    - **title**: the new title of the dataobj.
    """

    new_frontmatter = {
        "title": request.json.get("title"),
    }

    try:
        data.update_item_frontmatter(dataobj_id, new_frontmatter)
        return Response(status=200)
    except BaseException:
        return Response(status=404)


@api_bp.route("/dataobjs", methods=["GET"])
def get_dataobjs():
    """Gets all dataobjs"""
    cur_dir = data.get_items(structured=False, json_format=True)
    return jsonify(cur_dir)


@api_bp.route("/tags/add_to_index", methods=["PUT"])
def add_tag_to_index():
    """Add a tag to the database."""
    tag = request.json.get("tag", False)
    if tag and type(tag) is str and tags.is_tag_format(tag):
        if tags.add_tag_to_index(tag):
            return Response(status=200)
        else:
            return Response(status=404)

    return Response("Must provide valid tag name.", status=401)


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
        if not sanitized_name:
            return Response("Invalid dirname", status=400)
    except FileExistsError:
        return Response("Directory already exists", status=400)
    return Response(sanitized_name, status=200)


@api_bp.route("/folders/delete", methods=["DELETE"])
def delete_folder():
    """
    Deletes directory.

    Parameter in JSON body:
    - **path** of dir to delete
    """
    directory = request.json.get("path")
    if directory == "":
        return Response("Cannot delete root dir", status=401)
    if data.delete_dir(directory):
        return Response("Successfully deleted", status=200)
    return Response("Could not delete directory", status=400)


@api_bp.route("/search", methods=["GET"])
def search_endpoint():
    """
    Searches the instance.

    Request URL Parameter:
    - **query**
    """
    if not current_app.config["SEARCH_CONF"]["enabled"]:
        return Response("Search is disabled", status=401)
    query = request.args.get("query")
    search_results = search(query)
    return jsonify(search_results)


@api_bp.route("/images", methods=["POST"])
def image_upload():
    CONTENT_TYPES = ["image/jpeg", "image/png", "image/gif"]
    if "image" not in request.files:
        return jsonify({"error": "400"}), 400
    image = request.files["image"]
    if (
        data.valid_image_filename(image.filename)
        and image.headers["Content-Type"].strip() in CONTENT_TYPES
    ):
        saved_to = data.save_image(image)
        return jsonify({"data": {"filePath": f"/images/{saved_to}"}}), 200
    return jsonify({"error": "415"}), 415
