
![logo](https://github.com/Uzay-G/archivy/raw/master/logo.png)


# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

Features:

- CLI that provides a nice backend interface to the app
- Login module that allows you to host the service on a server
- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, following the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Backend API for flexibility and user enhancements
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL
- Allows you to sync up with Pocket to gather bookmarks from there too.
- Dark Theme


![demo (low res)](https://github.com/Uzay-G/archivy/raw/master/archivy.gif)


Upcoming:

- Plugin system to allow people to publish and write extensions to archivy
- Option to compile data to a static site that can be deployed.
- UI for grouping by tag and use NLP to automatically generate connections between posts

## Setup

### Local Setup

- Make sure your system has Python and pip installed.
- Install the python package with `pip install archivy`
- There you go! You should be able to start the app by running `archivy` in your terminal.

### Configuration

Archivy uses environment variables for its configuration:

| Variable                | Default                     | Description                           |
|-------------------------|-----------------------------|---------------------------------------|
| `ARCHIVY_DATA_DIR`      | System-dependant, see below | Directory in which data will be saved |
| `ARCHIVY_PORT`          | 5000                        | Port on which archivy will run        |
| `ELASTICSEARCH_ENABLED` | 0                           | Enable Elasticsearch integration      |
| `ELASTICSEARCH_URL`     | http://localhost:9200       | Url to the elasticsearch server       |


`ARCHIVY_DATA_DIR` by default will be set by the
[appdirs](https://pypi.org/project/appdirs/) python library:

On Linux systems, it follows the [XDG
specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):
`~/.local/share/archivy`


### With Docker

See the `docker` branch for details on setting things up with docker.

### Setting up Search

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

## Usage

The cli allows you to manage and run archivy:

```
Usage: archivy [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  routes  Show the routes for the app.
  run     Runs archivy web application
  shell   Run a shell in the app context.
```

The first time you run archivy, an admin user will automatically be created with a random password.
These credentials will be printed to the log when you launch like this:

```
[2020-10-10 10:48:27,764] INFO in __init__: Archivy has created an admin user as it did not exist.
                            Username: 'admin', password: '5a512991c605ea51038ce2a0'
```

Login with these credentials and then you can change your password/username by clicking the profile button on the top left.

You can then use archivy to create notes, organize it and store information.

## Scripting

You might be interested in extending archivy by for example building scripts that allow you to regularly fetch data or other functionalities. In that case you can use the [api system](https://github.com/Uzay-G/archivy/blob/master/API.md) and soon a [powerful plugin system](https://github.com/Uzay-G/archivy/issues/86).


## Community and Development

If you're interested in developing and improving Archivy, please join our [community discord server](https://discord.gg/uQsqyxB).

Feel free to [open issues](https://github.com/Uzay-G/archivy/issues/new) if you encounter bugs, have any ideas / feature requests and use the discord server for more casual discussion.
