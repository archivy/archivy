from pathlib import Path
from shutil import which
from subprocess import run, PIPE

from flask import current_app

from archivy.helpers import get_elastic_client


# Example command ["rg", RG_MISC_ARGS, RG_FILETYPE, RG_REGEX_ARG, query, str(get_data_dir())]
#  rg -il -t md -e query files
# -i -> case insensitive
# -l -> only output filenames
# -t -> file type
# -e -> regexp
RG_MISC_ARGS = "-ilt"
RG_REGEX_ARG = "-e"
RG_FILETYPE = "md"


def add_to_index(model):
    """
    Adds dataobj to given index. If object of given id already exists, it will be updated.

    Params:

    - **index** - String of the ES Index. Archivy uses `dataobj` by default.
    - **model** - Instance of `archivy.models.Dataobj`, the object you want to index.
    """
    es = get_elastic_client()
    if not es:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    es.index(
        index=current_app.config["SEARCH_CONF"]["index_name"], id=model.id, body=payload
    )
    return True


def remove_from_index(dataobj_id):
    """Removes object of given id"""
    es = get_elastic_client()
    if not es:
        return
    es.delete(index=current_app.config["SEARCH_CONF"]["index_name"], id=dataobj_id)


def query_es_index(query, strict=False):
    """
    Returns search results for your given query

    Specify strict=True if you want only exact result (in case you're using ES.
    """
    es = get_elastic_client()
    if not es:
        return []
    search = es.search(
        index=current_app.config["SEARCH_CONF"]["index_name"],
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"],
                    "analyzer": "rebuilt_standard",
                }
            },
            "highlight": {
                "fragment_size": 0,
                "fields": {"content": {"pre_tags": "==", "post_tags": "=="}},
            },
        },
    )

    hits = []
    for hit in search["hits"]["hits"]:
        formatted_hit = {"id": hit["_id"], "title": hit["_source"]["title"]}
        if "highlight" in hit:
            formatted_hit["highlight"] = hit["highlight"]["content"]
            reformatted_match = " ".join(formatted_hit["highlight"]).replace("==", "")
            if strict and not (query in reformatted_match):
                continue
        hits.append(formatted_hit)
    return hits


def query_ripgrep(query):
    """Uses ripgrep to search data with a simpler setup than ES"""

    from archivy.data import get_data_dir

    if current_app.config["SEARCH_CONF"]["engine"] != "ripgrep" or not which("rg"):
        return None

    rg_cmd = ["rg", RG_MISC_ARGS, RG_FILETYPE, RG_REGEX_ARG, query, str(get_data_dir())]
    rg = run(rg_cmd, stdout=PIPE, stderr=PIPE, timeout=60)
    file_paths = [Path(p.decode()).parts[-1] for p in rg.stdout.splitlines()]

    # don't open file just find info from filename for speed
    hits = []
    for filename in file_paths:
        parsed = filename.replace(".md", "").split("-")
        hits.append({"id": int(parsed[0]), "title": "-".join(parsed[1:])})
    return hits


def query_ripgrep_tags():
    """
    Uses ripgrep to search for tags.
    Mandatory reference: https://xkcd.com/1171/
    """

    # Simple idea:
    #  We look for `#` followed by characters that are not white-space
    #                  followed by a terminating white-space.
    # Problem: This also matches `####`
    # PATTERN = r"#(\S+)\W"

    # Still simple:
    # Match a `#` and then something that's not a `#`
    # Problem:
    #   String #####asd
    #   This matches #asd
    # Problem 2:
    # regex parse error:
    #     #(?!#)(\S+)\W
    #      ^^^
    # error: look-around, including look-ahead and look-behind, is not supported
    # PATTERN = r"#(?!#)(\S+)\W"

    # Not nice:
    # Problem: This only works for very limited character sets. Eg: #üöäèéàß doesn't match.
    # Problem2: This also matches parts of URLs and other things like embedded CSS
    # PATTERN = r"#([a-zA-Z0-9_-]+)"

    # Compromise: Allow "####tag"
    # PATTERN = r"#([\S0-9_-]+)"

    # I cave
    PATTERN = r"#([a-zA-Z0-9_-]+)\w"
    from archivy.data import get_data_dir

    if current_app.config["SEARCH_CONF"]["engine"] != "ripgrep" or not which("rg"):
        return None

    # io: case insensitive, only return matches
    rg_cmd = ["rg", "-ioI", RG_FILETYPE, RG_REGEX_ARG, PATTERN, str(get_data_dir())]
    rg = run(rg_cmd, stdout=PIPE, stderr=PIPE, timeout=60)
    tags = rg.stdout.splitlines()

    rg_cmd = ["rg", "-ioIc", RG_FILETYPE, RG_REGEX_ARG, PATTERN, str(get_data_dir())]
    rg = run(rg_cmd, stdout=PIPE, stderr=PIPE, timeout=60)
    counts = rg.stdout.splitlines()

    # rg returns a bytestring
    #  including the `#`
    return [str(t, "utf-8")[1:] for t in tags]


def search(query, strict=False):
    """
    Wrapper to search methods for different engines.

    If using ES, specify strict=True if you only want results that strictly match the query, without parsing / tokenization.
    """
    if current_app.config["SEARCH_CONF"]["engine"] == "elasticsearch":
        return query_es_index(query, strict=strict)
    elif current_app.config["SEARCH_CONF"]["engine"] == "ripgrep":
        return query_ripgrep(query)
