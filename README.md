![logo](docs/img/logo.png)


# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your own personal, searchable and extensible wiki.

Features:

- If you add bookmarks, their web-pages contents' will be saved to ensure that you will **always** have access to it, following the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Bidirectional links between notes.
- Login module that allows you to host the service on a server
- Plugin system to allow people to publish and write extensions to archivy
- [Git integration](https://github.com/archivy/archivy-git)
- Everything is a file! For ease of access and editing, all the content is stored in extended markdown files with yaml front matter. This format supports footnotes, LaTeX math rendering, syntax highlighting and more. 
- Powerful and advanced search. 
- Backend API for flexibility and user enhancements.
- Image upload

[demo video](https://www.uzpg.me/assets/images/archivy.mov)

[Roadmap](https://github.com/archivy/archivy/issues/74#issuecomment-764828063)

Upcoming:

- Annotations
- Multi User System with permission setup.

## Quickstart


Install archivy with `pip install archivy`. Other installations methods are listed [here](https://archivy.github.io/install), including Docker.

Run the `archivy init` command to setup you installation.

Then run this and enter a password to create a new user:

```bash
$ archivy create-admin <username>
```

Finally, execute `archivy run` to serve the app. You can open it at https://localhost:5000 and login with the credentials you entered before.

You can then use archivy to create notes, bookmarks and then organize and store information.

See the [official docs](https://archivy.github.io) for information on other installation methods.

## Community

Archivy is dedicated to building **open and quality knowledge base software** through collaboration and community discussion.

To get news and updates on Archivy and its development, you can [watch the archivy repository](https://github.com/archivy/archivy) or follow [@uzpg_ on Twitter](https://twitter.com/uzpg_).

You can interact with us through the [issue board](https://github.com/archivy/archivy/issues) and the more casual [discord server](https://discord.gg/uQsqyxB).
