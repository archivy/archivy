Archivy comes with a simple command line interface that you use on the backend to run archivy:

```
Usage: archivy [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  create-admin  Creates a new admin user
  routes        Show the routes for the app.
  run           Runs archivy web application
  shell         Run a shell in the app context.
```

Make sure you've configured Archivy by running `archivy init`, as outlined in [install](install.md).

If you'd like to add users, you can simply create new admin users with the `create-admin` command. Only give credentials to trusted people.

You can then use archivy to create notes, bookmarks and to organize and store information.

You can use the [web api](reference/web_api.md) to extend archivy, or [plugins](plugins.md).

These have been recently introduced, but you can check the existing plugins that you can install onto your instance [here](https://github.com/archivy/awesome-archivy).
