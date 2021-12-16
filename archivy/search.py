from pathlib import Path
from shutil import which
from subprocess import run, PIPE
import json

from flask import current_app

from archivy.helpers import get_elastic_client


# Example command ["rg", RG_MISC_ARGS, RG_FILETYPE, RG_REGEX_ARG, query, str(get_data_dir())]
#  rg -il -t md -e query files
# -i -> case insensitive
# -l -> only output filenames
# -t -> file type
# -e -> regexp
RG_MISC_ARGS = "-it"
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
                "fields": {
                    "content": {
                        "pre_tags": "",
                        "post_tags": "",
                    }
                },
            },
        },
    )

    hits = []
    for hit in search["hits"]["hits"]:
        formatted_hit = {"id": hit["_id"], "title": hit["_source"]["title"]}
        if "highlight" in hit:
            formatted_hit["matches"] = hit["highlight"]["content"]
            reformatted_match = " ".join(formatted_hit["matches"])
            if strict and not (query in reformatted_match):
                continue
        hits.append(formatted_hit)
    return hits


def query_ripgrep(query):
    """
    Uses ripgrep to search data with a simpler setup than ES.
    Returns a list of dicts with detailed matches.
    """

    from archivy.data import get_data_dir

    if not which("rg"):
        return None

    rg_cmd = ["rg", RG_MISC_ARGS, RG_FILETYPE, "--json", query, str(get_data_dir())]
    rg = run(rg_cmd, stdout=PIPE, stderr=PIPE, timeout=60)
    output = rg.stdout.decode().splitlines()
    hits = {}
    curr_id = -1
    for line in output:
        hit = json.loads(line)
        if hit["type"] == "begin":
            curr_file = (
                Path(hit["data"]["path"]["text"])
                .parts[-1]
                .replace(".md", "")
                .split("-")
            )  # parse target note data from path
            curr_id = int(curr_file[0])
            title = curr_file[-1].replace("_", " ")
            hits[curr_id] = {"title": title, "matches": [], "id": curr_id}
        elif hit["type"] == "match":
            match_text = hit["data"]["lines"]["text"].strip()
            if not match_text.startswith("tags: [") and not match_text.startswith(
                "title:"
            ):  # don't send matches on metadata
                hits[curr_id]["matches"].append(match_text)
    return sorted(
        list(hits.values()), key=lambda x: len(x["matches"]), reverse=True
    )  # sort by number of matches


def query_ripgrep_tags():
    """
    Uses ripgrep to search for tags.
    Mandatory reference: https://xkcd.com/1171/
    """

    PATTERN = r"(^|\n| )#([-_a-zA-ZÀ-ÖØ-öø-ÿ0-9]+)#"
    from archivy.data import get_data_dir

    if not which("rg"):
        return None

    # io: case insensitive
    rg_cmd = ["rg", "-Uio", RG_FILETYPE, RG_REGEX_ARG, PATTERN, str(get_data_dir())]
    rg = run(rg_cmd, stdout=PIPE, stderr=PIPE, timeout=60)
    hits = set()
    for line in rg.stdout.splitlines():
        tag = Path(line.decode()).parts[-1].split(":")[-1]
        tag = tag.replace("#", "").lstrip()
        hits.add(tag)
    return hits


def search(query, strict=False):
    """
    Wrapper to search methods for different engines.

    If using ES, specify strict=True if you only want results that strictly match the query, without parsing / tokenization.
    """
    if current_app.config["SEARCH_CONF"]["engine"] == "elasticsearch":
        return query_es_index(query, strict=strict)
    elif current_app.config["SEARCH_CONF"]["engine"] == "ripgrep" or which("rg"):
        return query_ripgrep(query)
