from flask import Response, jsonify, request, Blueprint, current_app

from archivy import data
from archivy.data import get_items
from archivy.models import DataObj

api_bp = Blueprint('api', __name__)


@api_bp.route("/bookmarks/<int:bookmark_id>")
def get_bookmark(bookmark_id):
    bookmark_post = data.get_item(bookmark_id)

    return jsonify(
        bookmark_id=bookmark_id,
        title=bookmark_post["title"],
        content=bookmark_post.content,
        md_path=bookmark_post["fullpath"],
    ) if bookmark_post is not None else Response(status=404)


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id):
    if data.get_item(bookmark_id) is None:
        return Response(status=404)
    data.delete_item(bookmark_id)
    return Response(status=204)


@api_bp.route("/bookmarks", methods=["GET"])
def get_bookmarks():
    # FIXME: only root directory because I'm lazy
    root_dir = get_items(collections=['bookmarks', 'pocket_bookmarks'])
    bookmarks = list()
    for bookmark_post in root_dir.child_files:
        bookmarks.append(dict(
            bookmark_id=bookmark_post['id'],
            title=bookmark_post["title"],
            content=bookmark_post.content,
            md_path=bookmark_post["path"],
        ))
    return jsonify({'bookmarks': bookmarks})


@api_bp.route("/bookmarks", methods=["POST"])
def create_bookmark():
    json_data = request.get_json()
    bookmark = DataObj(
        url=json_data['url'],
        desc=json_data['desc'],
        tags=json_data['tags'],
        path=json_data['path'],
        type="bookmarks",
    )
    bookmark.process_bookmark_url()
    bookmark_id = bookmark.insert()
    if bookmark_id:
        return jsonify(
            bookmark_id=bookmark_id,
        )
    return Response(status=400)


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["PUT"])
def change_bookmark(bookmark_id):
    current_app.logger.debug(f'Attempting to delete bookmark <{bookmark_id}>')
    return Response(status=501)
