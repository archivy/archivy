Archivy supports two search engines:

1. [Elasticsearch](https://www.elastic.co/) - an incredibly powerful solution that is however harder to install.
2. [ripgrep](https://github.com/BurntSushi/ripgrep), much more lightweight but also less powerful.

These allow archivy to index and provide full-text search on their knowledge bases. 

You can select these in the `archivy init` script, and the [the config docs](config.md) also has more information on this.

## Elasticsearch

Elasticsearch, is a complex and extendable search engine that returns high-quality results.

Instructions to install and run the service which needs to be running when you use Elasticsearch can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).


Append these two lines to your [elasticsearch.yml config file](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html):

```yaml
http.cors.enabled: true
http.cors.allow-origin: "http://localhost:5000"
```

Then, when you run `archivy init` simply specify you have enabled ES to integrate it with archivy.

You will now have full-text search on your knowledge base!

If you're adding ES to an existing knowledge base, use `archivy index` to sync any changes.

Elasticsearch can be a hefty dependency, so if you have any ideas for something more light-weight that could be used as an alternative, please share on [this thread](https://github.com/archivy/archivy/issues/13).

## Ripgrep

[Ripgrep](https://github.com/BurntSushi/ripgrep), on the other hand, is much more lightweight and small, but is also a bit limited in its functionality.

Follow [these instructions](https://github.com/BurntSushi/ripgrep#installation) to install ripgrep.

Then simply specify you want to use it during the `archivy init` script (or edit the config to add it).

