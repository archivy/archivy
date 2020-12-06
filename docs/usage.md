Archivy comes with a simple command line interface that you use on the backend to run archivy:

```
Usage: archivy [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  config        Open archivy config.
  create-admin  Creates a new admin user
  init          Initialise your archivy application
  run           Runs archivy web application
  shell         Run a shell in the app context.
```

Make sure you've configured Archivy by running `archivy init`, as outlined in [install](install.md).

If you'd like to add users, you can simply create new admin users with the `create-admin` command. Only give credentials to trusted people.

The `config` command allows you to play around with [configuration](config.md) and use `shell` if you'd like to play around with the archivy python API.

You can then use archivy to create notes, bookmarks and to organize and store information.

The [web api](reference/web_api.md) is also useful to extend archivy, or [plugins](plugins.md).

These have been recently introduced, but you can check the existing plugins that you can install onto your instance [here](https://github.com/archivy/awesome-archivy).