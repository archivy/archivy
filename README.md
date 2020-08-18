# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

Features:


- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, in sync with the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Allows you to sync up with Pocket to gather bookmarks from there too.
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL


![demo (low res)](https://github.com/Uzay-G/archivy/raw/master/archivy.gif)
Upcoming:

- Integrations with HN, Reddit, and many more.
- Add submodules for digital identity so archivy syncs to your hn upvoted posts, reddit saved, etc...
- Option to compile data to a static site that can be deployed.

## Setup

### Local Setup

- Make sure your system has Python installed.
- Clone the repository.
- `cd` into the project directory.
- create a virtual env by running `python3 -m venv venv/`.
- run `pip install -r requirements.txt` or `pip3`.
- execute the `start.sh` script
- see below for setting up search functionality


### With Docker

- Make sure that your system has Docker installed.

If you wish to test the image for yourself, you can run

```
docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/usr/src/app/data harshavardhanj/archivy:latest
```
and you can access the service at `http://localhost:5000/` on your browser. 

Also, if you wish to build the image on your own, there are `Dockerfile`s present in the repository.

Finally, there is a `docker-compose.yaml` file present which can be used instead of the long docker command previously mentioned.
You can run `docker-compose up -d -f ./docker-compose.yaml` which will bring up the Archivy service for you.

### Setting up Search

Archivy uses [ElasticSearch](https://www.elastic.co) to provide efficient full-text search.

Add these lines to your flaskenv:

```bash
ELASTICSEARCH_ENABLED=1
ELASTICSEARCH_URL=http://localhost:9200
```

Instructions to install and run the service are provided [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).


Append these two lines to your [elasticsearch.yml config file](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html):

```yaml
http.cors.enabled: true
http.cors.allow-origin: "http://localhost:5000"
```
