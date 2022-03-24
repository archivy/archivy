![logo](img/logo.png)

# Archivy

Archivy is a self-hostable knowledge repository that allows you to learn and retain information in your own personal and extensible wiki.

Features:

- If you add bookmarks, their web-pages contents' will be saved to ensure that you will **always** have access to it, following the idea of [digital preservation](https://jeffhuang.com/designed_to_last/). Archivy is also easily integrated with other services and your online accounts.
- Knowledge base organization with bidirectional links between notes, and embedded tags.
- Everything is a file! For ease of access and editing, all the content is stored in extended markdown files with yaml front matter. This format supports footnotes, LaTeX math rendering, syntax highlighting and more. 
- Extensible plugin system and API for power users to take control of their knowledge process
- [syncing options](https://github.com/archivy/archivy-git)
- Powerful and advanced search. 
- Image upload


<video src="https://www.uzpg.me/assets/images/archivy.mov" style="width: 100%" controls>
</video>

[Roadmap](https://github.com/archivy/archivy/issues/74#issuecomment-764828063)

Upcoming:

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

To get news and updates on Archivy and its development, you can [watch the archivy repository](https://github.com/archivy/archivy) or follow [@uzpg_ on Twitter](https://twitter.com/uzpg_).

You can interact with us through the [issue board](https://github.com/archivy/archivy/issues) and the more casual [discord server](https://discord.gg/uQsqyxB).

If you'd like to support the project and its development, you can also [sponsor](https://github.com/sponsors/Uzay-G/) the Archivy maintainer.


Note: If you're interested in the applications of AI to knowledge management, we're also working on this with [Espial](https://github.com/Uzay-G/espial).

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for more information.
The Archivy Logo is designed by [Roy Quilor](https://www.quilor.com/), licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0)

[Changelog](https://github.com/archivy/archivy/releases)


