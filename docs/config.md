Once you've [initialized](install.md) your archivy install, a yaml archivy config is automatically generated.

You can edit it by running `archivy config`.

Here's an overview of the different values you can set and modify.


### General

| Variable                | Default                     | Description                           |
|-------------------------|-----------------------------|---------------------------------------|
| `USER_DIR`      | System-dependent, see below. It is recommended to set this through `archivy init` | Directory in which markdown data will be saved |
| `INTERNAL_DIR` | System-dependent, see below | Directory where archivy internals will be stored (config, db...)
| `PORT`          | 5000                        | Port on which archivy will run        |
| `HOST`          | 127.0.0.1                   | Host on which the app will run. |


### Search

See [setup-search.md] for more information.

All of these options are children of the `SEARCH_CONF` object, like this in the `config.yml`:

```yaml
SEARCH_CONF:
  enabled:
  url:
  # ...
```
To use search, you first have to enable it either through the `archivy init` setup script or by modifying the `enabled` variable (see below).

Variables marked `ES only` in their description are only relevant when using the Elasticsearch engine.

| Variable                | Default                        | Description                           |
|-------------------------|--------------------------------|---------------------------------------|
| `enabled`               | 1                              |                                       |
| `engine`                | empty string                   | search engine you'd like to use. One of `["ripgrep", ["elasticsearch"]`|
| `url`                   | http://localhost:9200          | **[ES only]** Url to the elasticsearch server       |
| `search_conf`           | Long dict of ES config options | **[ES only]** Configuration of Elasticsearch [analyzer](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html), [mappings](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html) and general settings. |


`INTERNAL_DIR` and `USER_DIR` by default will be set by the
[appdirs](https://pypi.org/project/appdirs/) python library:

On Linux systems, it follows the [XDG
specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):
`~/.local/share/archivy`
