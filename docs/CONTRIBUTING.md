
This is a short guide on the things you should know if you'd like to contribute to Archivy.

## Setting up a dev environment.

- Fork the [archivy repo](https://github.com/archivy/archivy) and then clone the fork on your local machine.
- Create a virtual environment by running `python -m venv venv/`. This will hold all archivy dependencies.
- Run `source venv/bin/activate` to activate this new environment.
- Run `pip install requirements.txt` to download all dependencies.


If you'd like to work on an [existing issue](https://github.com/archivy/archivy/issues), please comment on the github thread for the issue to notify that you're working on it, and then create a new branch with a suitable name.

For example, if you'd like to work on something about "Improving the UI", you'd call it `improve_ui`. Once you're done with your changes, you can open a pull request and we'll review them.

**Do not** begin working on a new feature without first discussing it and opening an issue, as we might not agree with your vision.

If your feature is more isolated and specific, it can also be interesting to develop a [plugin](plugins.md) for it, in which case we can help you with any questions related to plugin development, and would be happy to list your plugin on [awesome-archivy](https://github.com/archivy/awesome-archivy).

Thanks for contributing!
