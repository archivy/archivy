import subprocess
from datetime import datetime

import markdown
import requests
from tinydb import Query, operations
from flask import render_template, flash, redirect, request, jsonify

from main import app, db
from main.models import DataObj
from main.forms import NewBookmarkForm, NewNoteForm, DeleteDataForm, PocketForm
from main import data
from main.search import remove_from_index, query_index 

@app.route("/")
@app.route("/index")
def index():
    dataobjs = data.get_items()
    return render_template("home.html", title="Home", dataobjs=dataobjs)

# TODO: refactor two following methods  
@app.route("/bookmarks/new", methods=["GET", "POST"])
def new_bookmark():
    form = NewBookmarkForm()
    form.path.choices = [(pathname, pathname) for pathname in data.get_dirs()]
    if form.validate_on_submit():
        bookmark = DataObj(
            url=form.url.data,
            desc=form.desc.data,
            tags=form.tags.data,
            path=form.path.data,
            type="bookmarks")
        id = bookmark.insert()
        if id:
            flash("Bookmark Saved!")
            return redirect(f"/dataobj/{id}")
    return render_template(
        "bookmarks/new.html",
        title="New Bookmark",
        form=form)


@app.route("/notes/new", methods=["GET", "POST"])
def new_note():
    form = NewNoteForm()
    form.path.choices = [(pathname, pathname) for pathname in data.get_dirs()]
    if form.validate_on_submit():
        note = DataObj(
            title=form.title.data,
            desc=form.desc.data,
            tags=form.tags.data,
            path=form.path.data,
            type="note")
        id = note.insert()
        if id:
            flash("Note Saved!")
            return redirect(f"/dataobj/{id}")
    return render_template(
        "/notes/new.html",
        title="New Note",
        form=form)


@app.route("/dataobj/<id>")
def show_dataobj(id):
    try:
        dataobj = data.get_item(id)
    except BaseException:
        flash("Data not found")
        return redirect("/")

    content = markdown.markdown(dataobj.content, extensions=["fenced_code"])
    return render_template(
        "dataobjs/show.html",
        title=dataobj["title"],
        dataobj=dataobj,
        content=content,
        form=DeleteDataForm())

@app.route("/dataobj/delete/<id>", methods=["DELETE", "GET"])
def delete_data(id):
    try:
        data.delete_item(id)
    except BaseException:
        flash("Data could not be found!")
        return redirect("/")
    flash("Data deleted!")
    return redirect("/")

@app.route("/folders/new", methods=["POST"])
def create_folder():
    directory = request.json.get("name")
    data.create_dir(directory)
    return "Successfully Created", 200


@app.route("/folders/delete", methods=["DELETE"])
def delete_folder():
    directory = request.json.get("name")
    if directory == "":
        return "Cannot delete root dir", 401
    if data.delete_dir(directory):
        return "Successfully deleted", 200
    return "Not found", 404

@app.route("/search", methods=["GET"])
def search_elastic():
    query = request.args.get("query")
    search_results = query_index("dataobj", query)
    return jsonify(search_results)

@app.route("/pocket", methods=["POST", "GET"])
def pocket_settings():
    form = PocketForm()
    pocket = Query()
    if form.validate_on_submit():
        if db.search(pocket.type == "pocket_key"):
            redirect("/parse_pocket")
        request_data = {
            "consumer_key": form.api_key.data,
            "redirect_uri": "http://localhost:5000/parse_pocket?new=1",
        }
        resp = requests.post(
            "https://getpocket.com/v3/oauth/request",
            json=request_data,
            headers={
                "X-Accept": "application/json",
                "Content-Type": "application/json"})
        new_data = {
            "type": "pocket_key",
            "consumer_key": form.api_key.data,
            "code": resp.json()["code"]}
        if db.search(pocket.type == "pocket_key"):
            db.insert(new_data)
        else:
            db.update(new_data, pocket.type == "pocket_key")
        flash("Settings Saved")
        return redirect(
            f"https://getpocket.com/auth/authorize?request_token={r.json()['code']}&redirect_uri=http://localhost:5000/parse_pocket?new=1")

    return render_template(
        "pocket/new.html",
        title="Pocket Settings",
        form=form)


@app.route("/parse_pocket")
def parse_pocket():
    pocket = db.search(Query().type == "pocket_key")[0]
    if request.args.get("new") == "1":
        auth_data = {
            "consumer_key": pocket["consumer_key"],
            "code": pocket["code"]}
        resp = requests.post(
            "https://getpocket.com/v3/oauth/authorize",
            json=auth_data,
            headers={
                "X-Accept": "application/json",
                "Content-Type": "application/json"})
        db.update(
            operations.set(
                "access_token",
                resp.json()["access_token"]),
            Query().type == "pocket_key")
        flash(f"{resp.json()['username']} Signed in!")

    pocket_data = {
        "consumer_key": pocket["consumer_key"],
        "access_token": pocket["access_token"],
        "sort": "newest"}

    # get date of latest call to pocket api
    since = datetime(1970, 1, 1)
    for post in data.get_items(types=["pocket_bookmark"], structured=False):
        date = datetime.strptime(post["date"].replace("-", "/"), "%x")
        since = max(date, since)

    since = datetime.timestamp(since)
    if since:
        pocket_data["since"] = since
    bookmarks = requests.post(
        "https://getpocket.com/v3/get",
        json=pocket_data).json()

    # api spec: https://getpocket.com/developer/docs/v3/retrieve
    for pocket_bookmark in bookmarks["list"].values():
        if int(pocket_boomark["status"]) != 2:
            desc = pocket_bookmark["excerpt"] if int(pocket_bookmark["is_article"]) else None
            bookmark = DataObj(
                desc=desc,
                url=pocket_bookmark["resolved_url"],
                date=datetime.now(),
                tags="",
                type="pocket_bookmarks")

            print(bookmark.insert())
    return redirect("/")


