# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

Features:

- Extensible search
- Markdown file support
- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, in sync with the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).


## Setup

- Make sure your system has Python installed.
- Clone the repository.
- `cd` into the project directory.
- run `pip install -r requirements.txt` or `pip3`.
- execute `FLASK_DEBUG=1 flask run`
- see below for setting up search functionality

### Setting up Search

Archivy uses [ElasticSearch](https://www.elastic.co) to provide efficient full-text search.

Instructions to install and run the service are provided [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).

If you are running elasticsearch, use `FLASK_DEBUG=1 ELASTICSEARCH_URL=http://localhost:xxxx flask run`, where the default port is `9200`.
