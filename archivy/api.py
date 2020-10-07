from flask import Response, jsonify, request, Blueprint, current_app

from archivy import data
from archivy.models import DataObj

api_bp = Blueprint('api', __name__)


@api_bp.route("/dataobjs/<int:dataobj_id>")
def get_dataobj(dataobj_id):
    dataobj = data.get_item(dataobj_id)

    return jsonify(
        dataobj_id=dataobj_id,
        title=dataobj["title"],
        content=dataobj.content,
        md_path=dataobj["fullpath"],
    ) if dataobj else Response(status=404)


@api_bp.route("/dataobjs/<int:dataobj_id>", methods=["DELETE"])
def delete_bookmark(dataobj_id):
    if not data.get_item(dataobj_id):
        return Response(status=404)
    data.delete_item(dataobj_id)
    return Response(status=204)


@api_bp.route("/dataobjs", methods=["GET"])
def get_dataobjs():
    cur_dir = data.get_items(structured=False, json_format=True)
    return jsonify(cur_dir)


@api_bp.route("/bookmarks", methods=["POST"])
def create_bookmark():
    json_data = request.get_json()
    bookmark = DataObj(
        url=json_data['url'],
        desc=json_data.get('desc'),
        tags=json_data.get('tags'),
        path=json_data.get("path", ""),
        type="bookmarks",
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


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["PUT"])
def change_bookmark(bookmark_id):
    current_app.logger.debug(f'Attempting to delete bookmark <{bookmark_id}>')
    return Response(status=501)

        
@api_bp.route("/dataobj/local_edit/<dataobj_id>", methods=["GET"])
def local_edit(dataobj_id):
    dataobj = data.get_item(int(dataobj_id))
    print(dataobj, dataobj["fullpath"])
    if dataobj:
        data.open_file(dataobj["fullpath"])
        return Response(status=200)
    return Response(status=404)
