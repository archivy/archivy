
This is a short guide on the things you should know if you'd like to contribute to Archivy.

## Setting up a dev environment

1. Fork the [archivy repo](https://github.com/archivy/archivy) and then clone the fork on your local machine.
2. ensure you have python 3.8 and pip3 installed. Check with `python3.8 --version` and `python3.8 -m pip --version`
3. install pipenv: `python3.8 -m pip install --user pipenv`
4. At the root of the archivy repo, run `python3.8 -m pipenv install --deploy`
5. You can now use your virtualenv with `python3.8 -m pipenv shell`
6. You can exit the shell by running `exit`

## Adding new pip packages

1. ensure your current working directory is at the root of the archivy repo
2. ensure you're not in pipenv shell. That is, you're not in the virtual environment

```bash
# to install a pip package that is a dependency for archivy
$ python3.8 -m pipenv install <package name>==<version>

# to install a pip package used for testing or dev work
$ python3.8 -m pipenv install --dev <package name>==<version>
```

## Running the dev server
```bash
# in the pipenv shell

$ export FLASK_APP=archivy/__init__.py
$ export FLASK_ENV=development
$ flask run
```

## Running cli commands
```bash
# in the pipenv shell

$ python -m archivy.cli --help
```


If you'd like to work on an [existing issue](https://github.com/archivy/archivy/issues), please comment on the github thread for the issue to notify that you're working on it, and then create a new branch with a suitable name.

For example, if you'd like to work on something about "Improving the UI", you'd call it `improve_ui`. Once you're done with your changes, you can open a pull request and we'll review them.

**Do not** begin working on a new feature without first discussing it and opening an issue, as we might not agree with your vision.

If your feature is more isolated and specific, it can also be interesting to develop a [plugin](plugins.md) for it, in which case we can help you with any questions related to plugin development, and would be happy to list your plugin on [awesome-archivy](https://github.com/archivy/awesome-archivy).

Thanks for contributing!
