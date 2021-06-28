Once you've [initialized](install.md) your archivy install, a yaml archivy config is automatically generated.

You can edit it by running `archivy config`.

Here's an overview of the different values you can set and modify.


### General

| Variable                | Default                     | Description                           |
|-------------------------|-----------------------------|---------------------------------------|
| `USER_DIR`      | System-dependent, see below. It is recommended to set this through `archivy init` | Directory in which markdown data will be saved |
| `INTERNAL_DIR`  | System-dependent, see below | Directory where archivy internals will be stored (config, db...)
| `PORT`          | 5000                        | Port on which archivy will run        |
| `HOST`          | 127.0.0.1                   | Host on which the app will run. |
| `DEFAULT_BOOKMARKS_DIR` | empty string (represents the root directory) | any subdirectory of the `data/` directory with your notes.
| `SITE_TITLE`    | Archivy                     | String value to be displayed in page title and headings. |

### Scraping

An in-progress configuration object to customize how you'd like bookmarking / scraping to work. The options are children of the `SCRAPING_CONF` object, like so:

```yaml
SCRAPING_CONF:
  save_images:
  ...
```

| Variable                | Default                     | Description                           |
|-------------------------|-----------------------------|---------------------------------------|
| `save_images` | False | If true, whenever you save a bookmark, every linked image will also be downloaded locally. |

### Theming

Configure the way your Archivy install looks.

These configuration options are children of the `THEME_CONF` object, like this:

```yaml
THEME_CONF:
  use_theme_dark:
  use_custom_css:
  custom_css_file:
```

| Variable | Default | Description |
|------|-------|----|
| `use_theme_dark` | false | Whether or not to load the dark version of the default theme CSS. |
| `use_custom_css` | false | Whether or not to load custom css from `custom_css_file` |
| `custom_css_file` | "" | Name of file to load in the `css/` subdirectory of your user directory (the one with your data or hooks). Create `css/` if it doesn't exist. |


### Search

See [Setup Search](setup-search.md) for more information.

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
