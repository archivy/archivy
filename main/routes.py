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
    bookmarks = data.get_items(type='bookmark')
    print(len(bookmarks))
    return render_template('home.html', title='Home', bookmarks=bookmarks)

@app.route('/bookmarks/new', methods=['GET', 'POST'])
def new_bookmark():
    form = NewBookmarkForm()
    if form.validate_on_submit():
        bookmark = DataObj(url=form.url.data, desc=form.desc.data, tags=form.tags.data, type="bookmark")
        id = bookmark.insert()
        if id:
            flash("Bookmark Saved!")
            return redirect(f"/bookmarks/{id}")
    return render_template('bookmarks/new.html', title='New Bookmark', form=form)

@app.route("/notes/new", methods=['GET', 'POST'])
@app.route('/bookmarks/<id>')
def show_bookmark(id):
    bookmark = db.get(doc_id=int(id))
    content = markdown.markdown(bookmark["content"])
    return render_template("bookmarks/show.html", title=bookmark["title"], bookmark=bookmark, content=content, form=DeleteDataForm())

@app.route('/pocket', methods=['POST', 'GET'])
def pocket_settings():
    form = PocketForm()
    Pocket = Query()
    if form.validate_on_submit():
        request_data = {'consumer_key': form.api_key.data,
                        'redirect_uri': 'http://localhost:5000/parse_pocket?new=1',
                        }
        r = requests.post("https://getpocket.com/v3/oauth/request", json=request_data, headers={'X-Accept': 'application/json', 'Content-Type': 'application/json'})
        new_data = {'type': 'pocket_key', 'consumer_key': form.api_key.data, 'code': r.json()['code']}
        if len(db.search(Pocket.type == "pocket_key")) == 0:
            db.insert(new_data)
        else:
            db.update(new_data, Pocket.type == "pocket_key")
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

    most_recent_time = 0
    for k, v in bookmarks["list"].items():
        date = datetime.utcfromtimestamp(int(v['time_added']))
        bookmark = DataObj(desc=v['excerpt'], url=v['resolved_url'], date=date, tags="", type="bookmark")
        bookmark.insert()

        most_recent_time = max(most_recent_time, int(v['time_added']))
    db.update(operations.set('since', most_recent_time), Pocket.type == "pocket_key")
    return redirect("/")

# @app.route("/dataobj/delete/<id>", methods=['DELETE', 'GET'])
# def delete_data(id):
#     try:
 #        db.remove(doc_ids = [int(id)])
 #    except:
  #       flash("Data could not be found!")
   #      return redirect("/")
# 
 #    remove_from_index("dataobj", int(id))
  #   flash("Data deleted!")
   #  return redirect("/")
