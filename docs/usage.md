Archivy comes with a simple command line interface that you use on the backend to run archivy:

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

You can then use archivy to create notes, bookmarks and then organize and store information.
