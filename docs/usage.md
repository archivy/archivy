Archivy comes with a simple command line interface that you use on the backend to run archivy:

```
Usage: archivy [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  config        Open archivy config.
  create-admin  Creates a new admin user
  format        Format normal markdown files for archivy.
  index         Sync content to Elasticsearch
  init          Initialise your archivy application
  run           Runs archivy web application
  shell         Run a shell in the app context.
  unformat      Convert archivy-formatted files back to normal markdown.
```

Make sure you've configured Archivy by running `archivy init`, as outlined in [install](install.md).

If you'd like to add users, you can simply create new admin users with the `create-admin` command. Only give credentials to trusted people.

If you have normal md files you'd like to migrate to archivy, move your files into your archivy data directory and then run `archivy format <filenames>` to make them conform to [archivy's formatting](/reference/architecture/#data-storage). Run `archivy unformat` to convert the other way around.

You can sync changes to files to the Elasticsearch index by running `archivy index` or by simply using the web editor which updates ES when you push a change.

The `config` command allows you to play around with [configuration](config.md) and use `shell` if you'd like to play around with the archivy python API.

You can then use archivy to create notes, bookmarks and to organize and store information.

The [web api](reference/web_api.md) is also useful to extend archivy, or [plugins](plugins.md).

These have been recently introduced, but you can check the existing plugins that you can install onto your instance [here](https://github.com/archivy/awesome-archivy).
