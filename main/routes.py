from main import app, db
from flask import render_template, flash, redirect, request
from main.models import DataObj
from main.forms import *
import markdown
import requests
import json
from main import data
from tinydb import Query, operations
from datetime import datetime
from main.search import *

@app.route('/')
@app.route('/index')
def index():
    dataobjs = data.get_items()
    return render_template('home.html', title='Home', dataobjs=dataobjs)


@app.route('/bookmarks/new', methods=['GET', 'POST'])
def new_bookmark():
    form = NewBookmarkForm()
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
        'bookmarks/new.html',
        title='New Bookmark',
        form=form)


@app.route("/notes/new", methods=['GET', 'POST'])
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
            redirect("/")
    return render_template(
        '/notes/new.html',
        title='New Note',
        form=form)
@app.route('/dataobj/<id>')
def show_dataobj(id):
    try:
        dataobj = data.get_item(id)
    except BaseException:
        flash("Data not found")
        return redirect("/")

    content = markdown.markdown(dataobj.content)
    return render_template(
        "bookmarks/show.html",
        title=dataobj["title"],
        dataobj=dataobj,
        content=content,
        form=DeleteDataForm())

@app.route("/folders/new", methods=["POST"])
def create_folder():
    dir = request.json.get("name")
    data.create_dir(dir)
    return "Successfully Created", 200

@app.route("/folders/delete", methods=["DELETE"])
def delete_folder():
    dir = request.json.get("name")
    if dir == "":
        return "Cannot delete root dir", 401
    elif data.delete_dir(dir):
        return "Successfully deleted", 200
    else:
        return "Not found", 404
    
@app.route('/pocket', methods=['POST', 'GET'])
def pocket_settings():
    form = PocketForm()
    Pocket = Query()
    if form.validate_on_submit():
        if not len(db.search(Pocket.type == "pocket_key")):
            redirect("/parse_pocket")
        request_data = {
            'consumer_key': form.api_key.data,
            'redirect_uri': 'http://localhost:5000/parse_pocket?new=1',
        }
        r = requests.post(
            "https://getpocket.com/v3/oauth/request",
            json=request_data,
            headers={
                'X-Accept': 'application/json',
                'Content-Type': 'application/json'})
        new_data = {
            'type': 'pocket_key',
            'consumer_key': form.api_key.data,
            'code': r.json()['code']}
        if len(db.search(Pocket.type == "pocket_key")) == 0:
            db.insert(new_data)
        else:
            db.update(new_data, Pocket.type == "pocket_key")
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
            'consumer_key': pocket['consumer_key'],
            'code': pocket['code']}
        r = requests.post(
            "https://getpocket.com/v3/oauth/authorize",
            json=auth_data,
            headers={
                'X-Accept': 'application/json',
                'Content-Type': 'application/json'})
        db.update(
            operations.set(
                'access_token',
                r.json()['access_token']),
            Query().type == "pocket_key")
        access_token = r.json()['access_token']
        flash(f"{r.json()['username']} Signed in!")
    pocket_data = {
        'consumer_key': pocket['consumer_key'],
        'access_token': pocket['access_token'],
        'sort': "newest"}

    since = datetime(1970, 1, 1)
    for post in data.get_items(types=['pocket_bookmark'], structured=False):
        date = datetime.strptime(post['date'].replace("-", "/"), "%x") 
        since = max(date, since)

    since = datetime.timestamp(since)
    if since: pocket_data['since'] = since
    bookmarks = requests.post("https://getpocket.com/v3/get", json=pocket_data).json()
   
    # api spec: https://getpocket.com/developer/docs/v3/retrieve
    for k, v in bookmarks["list"].items():
        if int(v['status']) != 2:
            desc = v['excerpt'] if int(v['is_article']) else None
            bookmark = DataObj(
                desc=desc,
                url=v['resolved_url'],
                date=datetime.now(),
                tags="",
                type="pocket_bookmarks")

            print(bookmark.insert())
    return redirect("/")


@app.route("/dataobj/delete/<id>", methods=['DELETE', 'GET'])
def delete_data(id):
    try:
        data.delete_item(id)
    except BaseException:
        flash("Data could not be found!")
        return redirect("/")
    remove_from_index("dataobj", int(id))
    flash("Data deleted!")
    return redirect("/")
