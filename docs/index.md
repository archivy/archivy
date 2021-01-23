
![logo](img/logo.png)

# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your own personal, searchable and extensible wiki.

Features:

- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, following the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Login module that allows you to host the service on a server
- Plugin system to allow people to publish and write extensions to archivy
- Notes are stored in an extended markdown format with footnotes, LaTeX math rendering, syntax highlighting and more. 
- CLI that provides a nice backend interface to the app
- Backend API for flexibility and user enhancements
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL
- Dark Theme


<video src="https://www.uzpg.me/assets/images/archivy.mov" style="width: 100%" controls>
</video>

[Roadmap](https://github.com/archivy/archivy/issues/74#issuecomment-764828063)

Upcoming:

- Links / tagging between different knowledge base items
- Image Upload
- Annotations
- Multi User System with permission setup.

## Quickstart


Install archivy with `pip install archivy`. Other installations methods are listed [here](https://archivy.github.io/install)

Then run this and enter a password to create a new user:

```bash
$ archivy create-admin <username>
```

Finally, execute `archivy run` to serve the app. You can open it at https://localhost:5000 and login with the credentials you entered before.

You can then use archivy to create notes, bookmarks and then organize and store information.

See [the docs](install.md) for information on other installation methods.

## Community

Archivy is dedicated at building **open and quality knowledge base software** through collaboration and community discussion.

You can interact with us through the [issue board](https://github.com/archivy/archivy/issues) and the more casual [discord server](https://discord.gg/uQsqyxB).

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for more information.
The Archivy Logo is designed by [Roy Quilor](https://www.quilor.com/), licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0)

[Changelog](https://github.com/archivy/archivy/releases)
