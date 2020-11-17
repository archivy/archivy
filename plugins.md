# Plugins

Plugins are a newly introduced method to add extensions to the archivy cli and web interface. It relies on the extremely useful [click-plugins](https://github.com/click-contrib/click-plugins) package that is loaded through pip and the [click-web](https://github.com/click-contrib/click-plugins) which has been modified and whose can be found in `archivy/click_web/`, some of the tests, templates and static files.


To help you understand the way the plugin system works, we're going to build our own plugin that allows users to sync content from `pocket`. We'll even deploy it to Pypi so that other people can install it.


Prerequisites: A python and pip installation with archivy.

## Step 1: Defining what our archivy extension does

`archivy` source used to have a built-in feature that allowed you to sync up to the bookmarks of your pocket account. We removed this and prefer to replace it with a standalone plugin, so let's build it!

What it will do is allow a user to download their bookmarks from pocket, without redownloading content that already exists.

## Step 2: Setting up the project

Make a new directory named `archivy_pocket` wherever you want on your system and create a new [`setup.py`](https://stackoverflow.com/questions/1471994/what-is-setup-py) file that will define the characteristics of our package.

This is what it looks like:

```python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='archivy_pocket',
    version='0.1.0',
    author="Uzay-G",
    author_email="halcyon@disroot.org",
    description=(
        "Archivy extension to sync content to your pocket account."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    entry_points='''
        [archivy.plugins]
        pocket=archivy_pocket:pocket
    '''
)
```

Let's walk through what this is doing. We are setting up our package and we define a few characteristics of the package. We specify some metadata you can adapt to your own package. We then load our package by using the `find_packages` function. The `entry_points` part is the most important. The `[archivy.plugins]` tells archivy that this package will extend our CLI and then we define the command we want to add. In our case, people will call the extension using `archivy pocket`. We will actually be creating a group so that people will call subcommands like this: `archivy pocket <subcommand>`. You can do things either way.

Create a `README.md` file that you can keep empty for now but should haCve information on your project.

## Step 3: Writing the core code of our plugin

Create an `archivy_web` directory inside the current directory where `setup.py` is stored. Create an `__init__.py` file in that directory where we'll store our main project code. For larger projects, it's better to separate concerns but that'll be good for now.

This is what the skeleton of our code looks will look like.

```python
import click # the package that manages the cli

@click.group()
def pocket():
    pass

@pocket.command()
def command1():
	...

@pocket.command()
def command2():
	...
```

With this structure, you'll be able to call `archivy pocket command1` and `archivy pocket command2`. Read the [click docs](https://click.palletsprojects.com/en/7.x/options/) to learn about how to build more intricate

Let's get into actually writing a command that interacts with the archivy codebase.

The code below does a few things:

- It imports the archivy `app` that basically is the interface for the webserver and many essential Flask features (flask is the web framework archivy uses).
- It imports the `get_db` function that allows us to access and modify the db.
- We define our pocket group.
- We create a new command from that group, what's important here is the `with app.app_context` part. We need to run our code inside the archivy `app_context` to be able to call some of the archivy methods. If you call archivy methods in your plugins, it might fail if you don't include this part.
- Then we just have our command code.


```python
import click
from archivy.extensions import get_db
from archivy import app
from archivy.data import get_items

@click.group()
def pocket():
    pass

@pocket.command()
@click.argument("api_key")
def auth(api_key):
    with app.app_context():
        db = get_db()
		# ...
```


We also added some other commands, but we'll skip them for brevity and you can check out the source code [here](https://github.com/archivy/archivy_pocket).

Now you just need to do `pip install .` in the main directory and you'll have access to the commands. Check it out by running `archivy --help`.

## Step 4: Publishing our package to Pypi

[Pypi](https://pypi.org) is the Python package repository. Publishing our package to it will allow other users to easily install our code onto their own archivy instance.

This is a short overview. Check out [this website](https://packaging.python.org/) for more info.

This section is inspired by [this](https://packaging.python.org/tutorials/packaging-projects/#installing-your-newly-uploaded-package).


Make sure the required utilities are installed:

```python
python3 -m pip install --user --upgrade setuptools wheel
```

Now run this command in the main dir to build the source:

```python
python3 setup.py sdist bdist_wheel
```

Now you need to create an account on [Pypi](https://pypi.org). Then go [here](https://pypi.org/manage/account/#api-tokens) and create a new API token; don’t limit its scope to a particular project, since you are creating a new project.


Once you've saved your token, install `twine`, the program that will take care of the upload:

```python
python3 -m pip install --user --upgrade twine
```

And you can finally upload your code! The username you should enter is `__token__` and then the password is your API token.

```python
python3 -m twine upload dist/*
```

