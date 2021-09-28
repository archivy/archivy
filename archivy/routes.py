from pathlib import Path
from os.path import sep
from pkg_resources import require

import frontmatter
from flask import (
    render_template,
    flash,
    redirect,
    request,
    url_for,
    send_file,
    send_from_directory,
)
from flask_login import login_user, current_user, logout_user
from tinydb import Query
from werkzeug.security import check_password_hash, generate_password_hash

from archivy.models import DataObj, User
from archivy import data, app, forms
from archivy.helpers import get_db, write_config
from archivy.tags import get_all_tags_with_counts, get_all_tags
from archivy.search import search
from archivy.config import Config


@app.context_processor
def pass_defaults():
    dataobjs = data.get_items()
    version = require("archivy")[0].version
    SEP = sep
    # check windows parsing for js (https://github.com/Uzay-G/archivy/issues/115)
    if SEP == "\\":
        SEP += "\\"
    return dict(dataobjs=dataobjs, SEP=SEP, version=version)


@app.before_request
def check_perms():
    allowed_path = (
        request.path.startswith("/login")
        or request.path.startswith("/static")
        or request.path.startswith("/api/login")
    )
    if not current_user.is_authenticated and not allowed_path:
        return redirect(url_for("login", next=request.path))
    return


@app.route("/")
@app.route("/index")
def index():
    path = request.args.get("path", "").lstrip("/")
    try:
        files = data.get_items(path=path)
    except FileNotFoundError:
        flash("Directory does not exist.", "error")
        return redirect("/")

    return render_template(
        "home.html",
        title=path or "root",
        search_enabled=app.config["SEARCH_CONF"]["enabled"],
        dir=files,
        current_path=path,
        new_folder_form=forms.NewFolderForm(),
        delete_form=forms.DeleteFolderForm(),
        rename_form=forms.RenameDirectoryForm(),
        view_only=0,
        search_engine=app.config["SEARCH_CONF"]["engine"],
    )


# TODO: refactor two following methods
@app.route("/bookmarks/new", methods=["GET", "POST"])
def new_bookmark():
    default_dir = app.config.get("DEFAULT_BOOKMARKS_DIR", "root directory")
    form = forms.NewBookmarkForm(path=default_dir)
    form.path.choices = [("", "root directory")] + [
        (pathname, pathname) for pathname in data.get_dirs()
    ]
    if form.validate_on_submit():
        path = form.path.data
        tags = form.tags.data.split(",") if form.tags.data != "" else []
        tags = [tag.strip() for tag in tags]
        bookmark = DataObj(url=form.url.data, tags=tags, path=path, type="bookmark")
        bookmark.process_bookmark_url()
        bookmark_id = bookmark.insert()
        if bookmark_id:
            flash("Bookmark Saved!", "success")
            return redirect(f"/dataobj/{bookmark_id}")
    # for bookmarklet
    form.url.data = request.args.get("url", "")
    path = request.args.get("path", default_dir).strip("/")
    # handle empty argument
    form.path.data = path
    return render_template("dataobjs/new.html", title="New Bookmark", form=form)


@app.route("/notes/new", methods=["GET", "POST"])
def new_note():
    form = forms.NewNoteForm()
    default_dir = "root directory"
    form.path.choices = [("", default_dir)] + [
        (pathname, pathname) for pathname in data.get_dirs()
    ]
    if form.validate_on_submit():
        path = form.path.data
        tags = form.tags.data.split(",") if form.tags.data != "" else []
        note = DataObj(title=form.title.data, tags=tags, path=path, type="note")
        note_id = note.insert()
        if note_id:
            flash("Note Saved!", "success")
            return redirect(f"/dataobj/{note_id}")
    path = request.args.get("path", default_dir).strip("/")
    # handle empty argument
    form.path.data = path
    return render_template("/dataobjs/new.html", title="New Note", form=form)


@app.route("/tags")
def show_all_tags():
    all_items = data.get_items(structured=False)
    all_tags_with_counts = get_all_tags_with_counts(all_items)

    list_of_tags = []
    for this_tag in list(all_tags_with_counts):
        list_of_tags.append({"tagname": this_tag, "count": all_tags[this_tag]["count"]})
    number_of_tags = len(list_of_tags)

    return render_template(
        "tags/all.html",
        title="All Tags",
        number_of_tags=number_of_tags,
        tags=sorted(list_of_tags, key=lambda k: k["count"], reverse=True),
    )


@app.route("/tags/<tag_name>")
def show_tag(tag_name):
    all_items = data.get_items(structured=False)

    # Fetch all tags from the dataobjs and count how often they appear.
    all_dataobjs = []
    for item in all_items:
        if tag_name in item["tags"]:
            all_dataobjs.append(item)

    return render_template(
        "tags/show.html",
        title=f"Tags - {tag_name}",
        tag_name=tag_name,
        all_dataobjs=all_dataobjs,
    )


@app.route("/dataobj/<dataobj_id>")
def show_dataobj(dataobj_id):
    dataobj = data.get_item(dataobj_id)

    if not dataobj:
        flash("Data could not be found!", "error")
        return redirect("/")

    if request.args.get("raw") == "1":
        return frontmatter.dumps(dataobj)

    backlinks = []
    if app.config["SEARCH_CONF"]["enabled"]:
        if app.config["SEARCH_CONF"]["engine"] == "ripgrep":
            query = f"/{dataobj_id}\)]]"  # escape query for rg
        else:
            query = f"/{dataobj_id})]]"
        incoming_links = search(query, strict=True)
        if incoming_links:
            for hit in incoming_links:
                if hit["id"] != dataobj_id:
                    backlinks.append({"title": hit["title"], "id": hit["id"]})

    # Form for moving data into another folder
    move_form = forms.MoveItemForm()
    move_form.path.choices = [("", "root directory")] + [
        (pathname, pathname) for pathname in data.get_dirs()
    ]

    post_title_form = forms.TitleForm()
    post_title_form.title.data = dataobj["title"]

    return render_template(
        "dataobjs/show.html",
        title=dataobj["title"],
        dataobj=dataobj,
        backlinks=backlinks,
        current_path=dataobj["dir"],
        form=forms.DeleteDataForm(),
        view_only=0,
        search_enabled=app.config["SEARCH_CONF"]["enabled"],
        post_title_form=post_title_form,
        move_form=move_form,
    )


@app.route("/dataobj/move/<dataobj_id>", methods=["POST"])
def move_item(dataobj_id):
    form = forms.MoveItemForm()
    out_dir = form.path.data if form.path.data != "" else "root directory"
    if form.path.data == None:
        flash("No path specified.")
        return redirect(f"/dataobj/{dataobj_id}")
    try:
        if data.move_item(dataobj_id, form.path.data):
            flash(f"Data successfully moved to {out_dir}.", "success")
            return redirect(f"/dataobj/{dataobj_id}")
        else:
            flash(f"Data could not be moved to {out_dir}.", "error")
            return redirect(f"/dataobj/{dataobj_id}")
    except FileNotFoundError:
        flash("Data not found.", "error")
        return redirect("/")
    except FileExistsError:
        flash("Data already in target directory.", "error")
        return redirect(f"/dataobj/{dataobj_id}")


@app.route("/dataobj/delete/<dataobj_id>", methods=["DELETE", "GET"])
def delete_data(dataobj_id):
    try:
        data.delete_item(dataobj_id)
    except BaseException:
        flash("Data could not be found!", "error")
        return redirect("/")
    flash("Data deleted!", "success")
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.UserForm()
    if form.validate_on_submit():
        db = get_db()
        user = db.search(
            (Query().username == form.username.data) & (Query().type == "user")
        )

        if user and check_password_hash(user[0]["hashed_password"], form.password.data):
            user = User.from_db(user[0])
            login_user(user, remember=True)
            flash("Login successful!", "success")

            next_url = request.args.get("next")
            return redirect(next_url or "/")

        flash("Invalid credentials", "error")
        return redirect("/login")
    return render_template("users/login.html", form=form, title="Login")


@app.route("/logout", methods=["DELETE", "GET"])
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect("/")


@app.route("/user/edit", methods=["GET", "POST"])
def edit_user():
    form = forms.UserForm()
    if form.validate_on_submit():
        db = get_db()
        db.update(
            {
                "username": form.username.data,
                "hashed_password": generate_password_hash(form.password.data),
            },
            doc_ids=[current_user.id],
        )
        flash("Information saved!", "success")
        return redirect("/")
    form.username.data = current_user.username
    return render_template("users/edit.html", form=form, title="Edit Profile")


@app.route("/folders/create", methods=["POST"])
def create_folder():
    form = forms.NewFolderForm()
    if form.validate_on_submit():
        path = Path(form.parent_dir.data.strip("/")) / form.new_dir.data
        new_path = data.create_dir(str(path))
        flash("Folder successfully created.", "success")
        return redirect(f"/?path={new_path}")
    flash("Could not create folder.", "error")
    return redirect(request.referrer or "/")


@app.route("/folders/delete", methods=["POST"])
def delete_folder():
    form = forms.DeleteFolderForm()
    if form.validate_on_submit():
        if data.delete_dir(form.dir_name.data):
            flash("Folder successfully deleted.", "success")
            return redirect("/")
        else:
            flash("Folder not found.", "error")
            return redirect(request.referrer or "/", 404)
    flash("Could not delete folder.", "error")
    return redirect(request.referrer or "/")


@app.route("/folders/rename", methods=["POST"])
def rename_folder():
    form = forms.RenameDirectoryForm()
    if form.validate_on_submit():
        try:
            new_path = data.rename_folder(form.current_path.data, form.new_name.data)
            if not new_path:
                flash("Invalid input.", "error")
            else:
                flash("Renamed successfully.", "success")
                return redirect(f"/?path={new_path}")
        except FileNotFoundError:
            flash("Directory not found.", "error")
        except FileExistsError:
            flash("Target directory exists.", "error")
    return redirect("/")


@app.route("/bookmarklet")
def bookmarklet():
    return render_template("bookmarklet.html", title="Bookmarklet")


@app.route("/images/<filename>")
def serve_image(filename):
    if filename and data.valid_image_filename(filename):
        image_path = data.image_exists(filename)
        if image_path:
            return send_file(image_path)
        else:
            return "Image not found", 404
    else:
        return "Invalid file request", 413


@app.route("/static/custom.css")
def custom_css():
    if not app.config["THEME_CONF"].get("use_custom_css", False):
        return ""
    return send_from_directory(
        Path(app.config["USER_DIR"]) / "css",
        app.config["THEME_CONF"]["custom_css_file"],
    )


@app.route("/config", methods=["GET", "POST"])
def config():
    """
    Web View to edit and update configuration.
    """

    def update_config_value(key, val, dictionary):
        if key != "SECRET_KEY":
            if type(val) is dict:
                for k, v in val.items():
                    update_config_value(k, v, dictionary[key])
            else:
                dictionary[key] = val

    form = forms.config_form(app.config)
    default = vars(Config())
    if form.validate_on_submit():
        changed_config = Config()
        changed_config.override(form.data)
        for k, v in vars(changed_config).items():
            # propagate changes to configuration
            update_config_value(k, v, app.config)
        write_config(vars(changed_config))  # save to filesystem config
        flash("Config successfully updated.", "success")
    elif request.method == "POST":
        flash("Could not update config.", "error")
    return render_template(
        "config.html", conf=form, default=default, title="Edit Config"
    )
