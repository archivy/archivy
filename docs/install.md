
## From pip

You can easily install archivy with `pip`. (pip  is the default package installer for Python, you can use pip to install many packages and apps, see this [link](https://pypi.org/project/pip/) for more information if needed)


- Make sure your system has Python, pip and [Pandoc](https://pandoc.org) installed. Pandoc allows us to convert between different formats and is an awesome tool. 
  - You can download Pandoc [here](https://pandoc.org/installing.html)
  - The Python programming language can be downloaded from [here](https://www.python.org/downloads/).
- Install the python package with `pip install archivy`
- Run `archivy create-admin <username>` to create a new user.
- There you go! You should be able to start the app by running `archivy run` in your terminal and then just login.

## With docker

You can also use archivy with Docker. 

See [Installing with docker](docker.md) for instructions on this.

We might implement an AppImage install. Comment [here](https://github.com/archivy/archivy/issues/44) if you'd like to see that happen.
