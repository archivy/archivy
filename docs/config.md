Archivy uses environment variables for its configuration (we are hesitating on this and might switch to a yaml file):

| Variable                | Default                     | Description                           |
|-------------------------|-----------------------------|---------------------------------------|
| `ARCHIVY_DATA_DIR`      | System-dependent, see below | Directory in which data will be saved |
| `ARCHIVY_PORT`          | 5000                        | Port on which archivy will run        |
| `ELASTICSEARCH_ENABLED` | 0                           | Enable Elasticsearch integration      |
| `ELASTICSEARCH_URL`     | http://localhost:9200       | Url to the elasticsearch server       |


`ARCHIVY_DATA_DIR` by default will be set by the
[appdirs](https://pypi.org/project/appdirs/) python library:

On Linux systems, it follows the [XDG
specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):
`~/.local/share/archivy`
