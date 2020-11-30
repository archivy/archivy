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

Make sure you've followed the steps in [install](install.md).

You can then use archivy to create notes, bookmarks and then organize and store information.

The `create-admin` command allows you to add new authorized admin users (only to people you trust), the `config` command to play around with [configuration](config.md) and `shell` if you'd like to play around with the archivy python API.
