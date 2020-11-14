import os

import frontmatter
import pypandoc
from tinydb import Query
from flask import render_template, flash, redirect, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user, logout_user

from archivy.models import DataObj, User
from archivy import data, app, forms
from archivy.helpers import get_db
from archivy.config import Config


@app.context_processor
def pass_defaults():
    dataobjs = data.get_items()
    SEP = os.path.sep
    # check windows parsing for js (https://github.com/Uzay-G/archivy/issues/115)
    if SEP == "\\":
        SEP += "\\"
    return dict(dataobjs=dataobjs, SEP=os.path.sep)


@app.before_request
def check_perms():
    allowed_path = (request.path.startswith("/login") or
                    request.path.startswith("/static") or
                    request.path.startswith("/api/login"))
    if not current_user.is_authenticated and not allowed_path:
        return redirect(url_for("login", next=request.path))
    return


@app.route("/")
@app.route("/index")
def index():
    return render_template(
            "home.html",
            title="Home",
            search_enabled=Config.ELASTICSEARCH_ENABLED,
            )


# TODO: refactor two following methods
@app.route("/bookmarks/new", methods=["GET", "POST"])
def new_bookmark():
    form = forms.NewBookmarkForm()
    form.path.choices = [(pathname, pathname) for pathname in data.get_dirs()]
    if form.validate_on_submit():
        path = form.path.data if form.path.data != "not classified" else ""
        bookmark = DataObj(
            url=form.url.data,
            desc=form.desc.data,
            tags=form.tags.data.split(","),
            path=path,
            type="bookmark")
        bookmark.process_bookmark_url()
        bookmark_id = bookmark.insert()
        if bookmark_id:
            flash("Bookmark Saved!")
            return redirect(f"/dataobj/{bookmark_id}")
    return render_template(
        "dataobjs/new.html",
        title="New Bookmark",
        form=form)


@app.route("/notes/new", methods=["GET", "POST"])
def new_note():
    form = forms.NewNoteForm()
    form.path.choices = [(pathname, pathname) for pathname in data.get_dirs()]
    if form.validate_on_submit():
        path = form.path.data if form.path.data != "not classified" else ""
        note = DataObj(
            title=form.title.data,
            desc=form.desc.data,
            tags=form.tags.data.split(","),
            path=path,
            type="note")
        note_id = note.insert()
        if note_id:
            flash("Note Saved!")
            return redirect(f"/dataobj/{note_id}")
    return render_template(
        "/dataobjs/new.html",
        title="New Note",
        form=form)


@app.route("/dataobj/<dataobj_id>")
def show_dataobj(dataobj_id):
    dataobj = data.get_item(dataobj_id)

    if not dataobj:
        flash("Data could not be found!")
        return redirect("/")

    if request.args.get("raw") == "1":
        return frontmatter.dumps(dataobj)

    extra_pandoc_args = ["--highlight-style="
                         + app.config['PANDOC_HIGHLIGHT_THEME'],
                         "--standalone"]

    content = pypandoc.convert_text(dataobj.content, 'html', format='md',
                                    extra_args=extra_pandoc_args)
    return render_template(
        "dataobjs/show.html",
        title=dataobj["title"],
        dataobj=dataobj,
        content=content,
        form=forms.DeleteDataForm())


@app.route("/dataobj/delete/<dataobj_id>", methods=["DELETE", "GET"])
def delete_data(dataobj_id):
    try:
        data.delete_item(dataobj_id)
    except BaseException:
        flash("Data could not be found!")
        return redirect("/")
    flash("Data deleted!")
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.UserForm()
    if form.validate_on_submit():
        db = get_db()
        user = db.search((Query().username == form.username.data) & (Query().type == "user"))

        if user and check_password_hash(user[0]["hashed_password"], form.password.data):
            user = User.from_db(user[0])
            login_user(user, remember=True)
            flash("Login successful!")

            next_url = request.args.get("next")
            return redirect(next_url or "/")

        flash("Invalid credentials")
        return redirect("/login")
    return render_template("users/form.html", form=form, title="Login")


@app.route("/logout", methods=["DELETE"])
@login_required
def logout():
    logout_user()
    flash("Logged out successfully")
    return redirect("/")


@app.route("/user/edit", methods=["GET", "POST"])
@login_required
def edit_user():
    form = forms.UserForm()
    if form.validate_on_submit():
        db = get_db()
        db.update(
            {
                "username": form.username.data,
                "hashed_password": generate_password_hash(form.password.data)
            },
            doc_ids=[current_user.id]
        )
        flash("Information saved!")
        return redirect("/")
    form.username.data = current_user.username
    return render_template("users/form.html", title="Edit Profile", form=form)
