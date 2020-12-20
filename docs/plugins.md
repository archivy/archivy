# Plugins

Plugins are a newly introduced method to add extensions to the archivy cli and web interface. It relies on the extremely useful [click-plugins](https://github.com/click-contrib/click-plugins) package that is loaded through pip and the [click-web](https://github.com/click-contrib/click-plugins) which has been modified and whose can be found in `archivy/click_web/`, some of the tests, templates and static files.

To help you understand the way the plugin system works, we're going to build our own example plugin. We'll even deploy it to Pypi so that other people can install it.

Note: The source code for this plugin is available [here](https://github.com/archivy/archivy/tree/master/docs/example_plugin).

We also recommend you read [the overview of the reference](reference/architecture.md) beforehand so you can better use the wrapper methods archivy exposes.

Prerequisites: A python and pip installation with archivy.

## Step 1: Defining what our archivy extension does

Let's build a simple plugin that will automatically add some metadata (author name, location...) at the end of each note.

## Step 2: Setting up the project

Make a new directory named `archivy_extra_metadata` that will be our plugin directory and create a new [`setup.py`](https://stackoverflow.com/questions/1471994/what-is-setup-py) file that will define the characteristics of our package.


Note: Using [`frontmatter`](https://archivy.github.io/reference/architecture/#data-storage) is better suited for this functionality, but here we'll just want something simple that adds text directly at the end of the content, like: `Made by John Doe in London.`

This is what our `setup.py` looks like:

```python

from setuptools import setup, find_packages

setup(
    name='archivy_extra_metadata',
    version='0.1.0',
    author="Uzay-G",
    description=(
        "Archivy extension to add some metadata at the end of your notes / bookmarks."
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    entry_points='''
        [archivy.plugins]
        extra-metadata=archivy_extra_metadata:extra_metadata
    '''
)
```

Let's walk through what this is doing:

- We specify some metadata you can adapt to your own package like `name`, `author` and `description`. 
- We then load our package and source code by using the `find_packages` function.
- The `entry_points` is the most important: the `[archivy.plugins]` part tells archivy that this package's commands will directly extend the archivy CLI so we can call `archivy extra-metadata` in the command line. We will actually be creating a group of commands so users will call subcommands like this: `archivy extra-metadata <subcommand>`. You can do things either way.

## Step 3: Writing the core code of our plugin

Create an `archivy_extra_metadata` directory inside the current directory where `setup.py` is stored. Create an `__init__.py` file in that directory where we'll store our main project code. For larger projects, it's better to separate concerns but that'll be good for now.

This will be the skeleton structure of our `__init__.py`:

```python
import click # the package that manages the cli

@click.group()
def extra_metadata():
    pass

@extra_metadata.command()
def command1():
	...

@extra_metadata.command()
def command2():
	...
```

With this example structure, you'd be able to run commands like `archivy extra_metadata command1` and `archivy extra_metadata command2`. Read the [click docs](https://click.palletsprojects.com/en/7.x/options/) to learn about how to build more intricate commands / options. We also provide some custom [option types](https://click.palletsprojects.com/en/7.x/parameters/#parameter-types) like [email and password](/reference/web_inputs.md)

Let's get into actually writing a command that interacts with the archivy codebase.

We'll make a command called `setup` to allow users to setup their metadata by specifying their name and location:

```python
import click
from archivy.helpers import get_db
from archivy import app

@click.group()
def extra_metadata():
    """`archivy_extra_metadata` plugin to add metadata to your notes."""
    pass

@extra_metadata.command()
@click.option("--author", required=True)
@click.option("--location", required=True)
def setup(author, location):
    """Save metadata values."""    
    with app.app_context():
        # save data in db
        get_db().insert({"type": "metadata", "author": author, "location": location})
    click.echo("Metadata saved!")
```

The code above does a few things:

- It imports the archivy `app` that is basically the interface for the webserver and many essential Flask features (flask is the web framework archivy uses).
- It imports the `get_db` function that allows us to access and modify the database.
- We define our `extra_metadata` group of commands that will be the parent of our subcommands.
- We create a new command from that group with two parameters: `author` and `location`. An important part of the code is the `with app.app_context()` part, we need to run our code inside the archivy `app_context` to be able to call some of the archivy methods. If you call archivy methods in your plugins, it might fail if you don't include this part.
- Then we just have our command code that takes the arguments and saves them into the [database](/reference/architecture/#data-storage).


Now you just need to do `pip install .` in the main directory and you'll have access to the commands. Check it out by running `archivy extra_metadata --help` and then you can access the commands:

```shell
$ archivy extra-metadata --help
Usage: archivy extra-metadata [OPTIONS] COMMAND [ARGS]...

  `archivy_extra_metadata` plugin to add metadata to your notes.

Options:
  --help  Show this message and exit.

Commands:
  setup  Save metadata values.

$ archivy extra-metadata setup --help
Usage: archivy extra-metadata setup [OPTIONS]

  Save metadata values.

Options:
  --name TEXT      [required]
  --location TEXT  [required]
  --help           Show this message and exit.

$ archivy extra-metadata setup --author Uzay --location Europe
Metadata saved!
```


That's nice and all, but now we want to actually use this metadata! This wouldn't work with a cli command, because we want it to add metadata whenever a new note is created, not just when a command is executed.

To do this, we'll use [`hooks`](/reference/hooks). These allow the end user to configure what happens whenever an event is fired off, like the creation of a [DataObj](reference/models.md) .

Archivy saves a link to a user-specified directory where it stores all your data for Archivy. This directory is usually set during the execution of the `archivy init` command.

It has this structure:

```
data/
	# content
```

Creating a `hooks.py` file in the root of this directory is how archivy calls these events.

For example, this could be a potential hook file:

```
# import base hooks that our `Hooks` class inherits
from archivy.config import BaseHooks

class Hooks(BaseHooks):
	def on_dataobj_create(self, dataobj):
		print("New dataobj created!")
```

What we'll be doing is we'll use the [`before_dataobj_create`](reference/hooks.md) event to add our metadata before the text is saved.

Let's define a function at the end of the `__init__.py` file of our package that takes a [DataObj](reference/models.md) as an argument and modifies it:

```
from tinydb import Query # this is the db handler that we use and we need to make a Query
def add_metadata(dataobj):
	with app.app_context():
		metadata = get_db().search(Query().type == "metadata")
		dataobj.content += f"Made by {metadata['author']} in {metadata['location']}"
```

Combined with our previous code:

```python
import click
from tinydb import Query
from archivy.helpers import get_db
from archivy import app

@click.group()
def extra_metadata():
    """`archivy_extra_metadata` plugin to add metadata to your notes."""
    pass

@extra_metadata.command()
@click.option("--author", required=True)
@click.option("--location", required=True)
def setup(author, location):
    """Save metadata values."""    
    with app.app_context():
        # save data in db
        get_db().insert({"type": "metadata", "author": author, "location": location})
    click.echo("Metadata saved!")


def add_metadata(dataobj):
	with app.app_context():
		metadata = get_db().search(Query().type == "metadata")[0]
		dataobj.content += f"\nMade by {metadata['author']} in {metadata['location']}."
```

Now to enable our plugin, all people have to do is modify their `hooks.py` file like this for example:

```python
from archivy_extra_metadata import add_metadata
from archivy.config import BaseHooks

class Hooks:
	def before_dataobj_create(self, dataobj):
		add_metadata(dataobj)
```

Users of your plugin will add the `add_metadata(dataobj)` to the `before_dataobj_create` call, and the metadata will be added automatically when the event is called.

We now have a working setup:

This is how our plugin will be used:

- Users install the package.
- They run `archivy extra-metadata setup --author xxx --location xxx` to set metadata.
- They modify their `hooks.py` to call `add_metadata` on the `before_dataobj_create` event.
- Voilà!

However, we need a way for them to install this package. That brings us to Step 4.

## Step 4: Publishing our package to Pypi

[Pypi](https://pypi.org) is the Python package repository. Publishing our package to it will allow other users to easily install our code onto their own archivy instance.

This is a short overview of how you can upload your package. Check out [this website](https://packaging.python.org/) for more info.

This section is inspired by [this useful tutorial](https://packaging.python.org/tutorials/packaging-projects/#installing-your-newly-uploaded-package).


Make sure the required utilities are installed:

```python
python3 -m pip install --user --upgrade setuptools wheel
```

Now run this command in the main directory to build the source:

```python
python3 setup.py sdist bdist_wheel
```

Create an account on [Pypi](https://pypi.org). Then go [here](https://pypi.org/manage/account/#api-tokens) and create a new API token; set its scope to all projects.


Once you've saved your token, install `twine`, the program that will take care of the upload:

```python
python3 -m pip install --user --upgrade twine
```

And you can finally upload your code! The username you should enter is `__token__` and then the password is your API token.

```python
python3 -m twine upload dist/*
```

## You're done!

Now that you've finished your package, you can share it if you'd like, publish it on a public git repository so other people can collaborate, and you can add it to the [`awesome_archivy` github repo](https://github.com/archivy/awesome-archivy) which is an official list of plugins built around Archivy.

We'd also love to hear about it on our [discord server](https://discord.gg/uQsqyxB)!
