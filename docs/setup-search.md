
Archivy supports two search engines:

1. [lunr](https://lunrjs.com), used by default, with a bit less flexibility but no effort to setup.
2. [Elasticsearch](https://www.elastic.co/) - an incredibly powerful solution that is however harder to install.

These allow archivy to to index and provide full-text search on their knowledge bases. 

See [the config docs](config.md) for information on how to select search engines.

## Lunr

Lunr comes already setup with your Archivy installation. It works out of the box.

## Elasticsearch

Elasticsearch, requires more effort but also returns better results.

Instructions to install and run the service which needs to be running when you use Elasticsearch can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).

Append these two lines to your [elasticsearch.yml config file](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html):

```yaml
http.cors.enabled: true
http.cors.allow-origin: "http://localhost:5000"
```

Then, when you run `archivy init` simply specify you have enabled ES to integrate it with Archivy.

You will now have full-text search on your knowledge base!

## Indexing

Archivy stores content as plain files, but this means that if you edit the file directly (not through search), the search index will not be up to date. To update it you have to run `archivy index`, and on top of this it will be automatically updated when you run the Archivy if you use Lunr.

If you use Archivy's web editor, the changes **will** be saved for search.


Check the [configuration](config.md) for ways to modify your search config.
