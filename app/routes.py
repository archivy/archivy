from app import app
from flask import render_template, flash, redirect
from app.models import Bookmark
from app.forms import NewBookmarkForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/bookmarks/new', methods=['GET', 'POST'])
def new_bookmark():
    form = NewBookmarkForm()
    if form.validate_on_submit():
        bookmark = Bookmark(False, url=form.url.data, desc=form.desc.data, content="Random", title="Title")
        if bookmark.insert():
            flash("Bookmark Saved!")
            return redirect("/")
    return render_template('bookmarks/new.html', title='New Bookmark', form=form)

