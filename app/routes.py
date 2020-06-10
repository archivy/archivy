from app import app, db
from flask import render_template, flash, redirect, request
from app.models import Bookmark
from app.forms import NewBookmarkForm, PocketForm
import markdown
import requests
import json
from tinydb import Query, operations
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    bookmark = Query()
    bookmarks = db.search(bookmark.type == "bookmark")
    return render_template('index.html', title='Home', bookmarks=bookmarks)

@app.route('/bookmarks/new', methods=['GET', 'POST'])
def new_bookmark():
    form = NewBookmarkForm()
    if form.validate_on_submit():
        bookmark = Bookmark(False, url=form.url.data, desc=form.desc.data, tags=form.tags.data)
        id = bookmark.insert()
        if id:
            flash("Bookmark Saved!")
            return redirect(f"/bookmarks/{id}")
    return render_template('bookmarks/new.html', title='New Bookmark', form=form)

@app.route('/bookmarks/<id>')
def show_bookmark(id):
    bookmark = db.get(doc_id=int(id))
    content = markdown.markdown(bookmark["content"])
    return render_template("bookmarks/show.html", title=bookmark["title"], bookmark=bookmark, content=content)

@app.route('/pocket', methods=['POST', 'GET'])
def pocket_settings():
    form = PocketForm()
    if form.validate_on_submit():
        request_data = {'consumer_key': form.api_key.data,
                        'redirect_uri': 'http://localhost:5000/parse_pocket?new=1',
                        }
        r = requests.post("https://getpocket.com/v3/oauth/request", json=request_data, headers={'X-Accept': 'application/json', 'Content-Type': 'application/json'})
        db.insert({'type': 'pocket_key', 'consumer_key': form.api_key.data, 'code': r.json()['code']})
        flash("Settings Saved")
        return redirect(f"https://getpocket.com/auth/authorize?request_token={r.json()['code']}&redirect_uri=http://localhost:5000/parse_pocket?new=1")

    return render_template("pocket/new.html", title="Pocket Settings", form=form)


@app.route("/parse_pocket")
def parse_pocket():
    Pocket = Query()
    pocket = db.search(Pocket.type == "pocket_key")[0]
    if request.args.get("new") == "1":
        auth_data = {'consumer_key': pocket['consumer_key'], 'code': pocket['code']}
        r = requests.post("https://getpocket.com/v3/oauth/authorize", json=auth_data, headers={'X-Accept': 'application/json', 'Content-Type': 'application/json'})
        print(r.text)
        db.update(operations.set('access_token', r.json()['access_token']), Pocket.type == "pocket_key")
        flash(f"{r.json()['username']} Signed in!")
    data = {'consumer_key': pocket['consumer_key'], 'access_token': r.json()['access_token'], 'sort': "newest"}
    if 'since' in pocket:
        data['since'] = pocket['since']
    bookmarks = requests.post("https://getpocket.com/v3/get", json=data).json()
    #return bookmarks['list']
    most_recent_time = 0
    for k, v in bookmarks["list"].items():
        date = datetime.utcfromtimestamp(int(v['time_added']))
        bookmark = Bookmark(None, desc=v['excerpt'], url=v['resolved_url'], date=date, tags="")
        bookmark.insert()

        most_recent_time = max(most_recent_time, int(v['time_added']))
    db.update(operations.set('since', most_recent_time), Pocket.type == "pocket_key")
    return redirect("/")

@app.route("/search")
def search():
    DataObj = Query()
    return render_template("search.html", json=db.search(DataObj.type == "bookmark"), title="Search")
