## With pip

You can easily install archivy with `pip`. (pip  is the default package installer for Python, you can use pip to install many packages and apps, see this [link](https://pypi.org/project/pip/) for more information if needed)


1. Make sure your system has Python and pip installed. The Python programming language can also be downloaded from [here](https://www.python.org/downloads/).
2. Install the python package with `pip install archivy`
3. If you'd like to use search, follow [these docs](setup-search.md) first and then do this part. Either way, run `archivy init` to create a new user and use the setup wizard.
4. There you go! You should be able to start the app by running `archivy run` in your terminal and then just login.

## With Nix
```ShellSession
$ nix-env -i archivy
```

## With docker

You can also use archivy with Docker. 

See [the docker documentation](https://github.com/archivy/archivy-docker) for instructions on this.

We might implement an AppImage install. Comment [here](https://github.com/archivy/archivy/issues/44) if you'd like to see that happen.
