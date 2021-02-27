## With pip

You can easily install archivy with `pip`. (pip  is the default package installer for Python, you can use pip to install many packages and apps, see this [link](https://pypi.org/project/pip/) for more information if needed)


1. Make sure your system has Python and pip installed. The Python programming language can also be downloaded from [here](https://www.python.org/downloads/).
2. Install the python package with `pip install archivy`
3. If you'd like to use search, follow [these docs](setup-search.md) first and then do this part. Either way, run `archivy init` to create a new user and use the setup wizard.
4. There you go! You should be able to start the app by running `archivy run` in your terminal and then just login.

## To run as a WSGI app using Gunicorn

1. Follow steps 1 to 3 from the above "With pip" Section.
2. install gunicorn with `pip install gunicorn`
3. Once archivy has been initialized, you can run it using gunicorn by running `gunicorn 'archivy.cli:create_app_with_cli()'`
4. If you wish, you can use the file `gunicorn.conf.py` at the root of the Archivy git repo as a good configuration starting point. You can explicitly use it by running `gunicorn -c gunicorn.conf.py 'archivy.cli:create_app_with_cli()'`

## With Nix
```ShellSession
$ nix-env -i archivy
```

## With docker

You can also use archivy with Docker. 

See [the docker documentation](https://github.com/archivy/archivy-docker) for instructions on this.

We might implement an AppImage install. Comment [here](https://github.com/archivy/archivy/issues/44) if you'd like to see that happen.
