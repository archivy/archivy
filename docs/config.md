Once you've [initialized](install.md) your archivy install, an archivy config is automatically generated. You can edit it through the archivy interface by clicking on the gear icon on the top right of the navbar, or by running `archivy config` in your terminal.

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

If you want to configure the scraping progress more, you can also create a `scraping.py` file in the root of your user directory. This file allows you to override the default bookmarking behavior for certain websites / links, which you can match with regex.

Once it matches a link, you can either pass your own custom function for parsing, or simply pass a string, which corresponds to the CSS selector for the part of the page you want archivy to scrape. If there are several matches, only the first will be treated.

Example that processes youtube videos:

```python
def process_videos(data):
	url = data.url
	# modify whatever you want / set the metadata
	data.title = "Video - " + url
	data.tags = ["video"]
	data.content = "..."

# declare your patterns in this PATTERNS variable
PATTERNS = {
	"*youtube.com/*": process_videos
}
```

With this example, whenever you create a bookmark of a youtube video, instead of going through the default archival, your function will be called on the data.


Example that tells archivy only to scrape the main body of Wikipedia pages:

```python
PATTERNS = {
	"https://*.wikipedia.org/wiki/*": "#bodyContent"
}
```

Example patterns:

- `*wikipedia*` (`*` matches everything)
- `https://duckduckg?.com*` (? matches a single character)
- `https://www.[nl][ya]times.com` ([] matches any character inside the brackets. Here it'll match nytimes or latimes, for example. Use ![] to match any character **not** inside the brackets)

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
| `es_user` and `es_password` | None | If you're using authentication, for example with a cloud-hosted ES install, you can specify a user and password |
| `es_processing_conf`           | Long dict of ES config options | **[ES only]** Configuration of Elasticsearch [analyzer](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html), [mappings](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html) and general settings. |


`INTERNAL_DIR` and `USER_DIR` by default will be set by the
[appdirs](https://pypi.org/project/appdirs/) python library:

On Linux systems, it follows the [XDG
specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):
`~/.local/share/archivy`


### Editor configuration
Archivy uses the [markdown-it](https://github.com/markdown-it/markdown-it) parser for its editor. This parser can be configured to change the output according to your needs. The default values of `EDITOR_CONF` are given below. Refer to the [markdown-it docs](https://github.com/markdown-it/markdown-it#init-with-presets-and-options) for a full list of possible options.

```yaml
EDITOR_CONF:
  settings:
    linkify: true
    html: false
    xhtmlOut: false
    breaks: true
    typographer: false
  plugins: ...
  toolbar_icons: ["bold", "italic", "link", "upload-image", "heading", "code", "strikethrough", "quote", "table"] # see https://github.com/Ionaru/easy-markdown-editor#toolbar-icons for more options
```

Archivy uses several markdown plugins to enhance its functionality:

- [markdown-it-anchor](https://github.com/valeriangalliat/markdown-it-anchor)
- [markdown-it-toc-done-right](https://github.com/nagaozen/markdown-it-toc-done-right)
- [markdown-it-mark](https://github.com/markdown-it/markdown-it-mark)
- [markdown-it-footnote](https://github.com/markdown-it/markdown-it-footnote)
- [markdown-it-texmath](https://github.com/goessner/markdown-it-texmath)

Some of these plugins (see below) can be configured and modified. Refer to their homepages above to see what you can change. They are set up with the following configuration by default:

```yaml
EDITOR_CONF:
  plugins:
    markdownitFootnote: {}
    markdownitMark: {}
    markdownItAnchor:
      permalink: True
      permalinkSymbol: '¶'
    markdownItTocDoneRight: {}
```
