Archivy uses [ElasticSearch](https://www.elastic.co) to provide efficient full-text search.

Instructions to install and run the service are provided [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).


Append these two lines to your [elasticsearch.yml config file](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html):

```yaml
http.cors.enabled: true
http.cors.allow-origin: "http://localhost:5000"
```

Run archivy like this:

```bash
ELASTICSEARCH_ENABLED=1 archivy run
```

You will now have full-text search on your knowledge base!

Whenever you edit an item through the files, it is better to have archivy running that way your changes will be synced to Elasticsearch.


Elasticsearch can be a hefty dependency, so if you have any ideas for something more light-weight that could be used as an alternative, please share on [this thread](https://github.com/archivy/archivy/issues/13).
