
![logo](img/logo.png)

Logo design by [Roy Quilor](https://www.quilor.com/) is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0)

# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

Features:

- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, following the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Login module that allows you to host the service on a server
- Plugin system to allow people to publish and write extensions to archivy
- CLI that provides a nice backend interface to the app
- Backend API for flexibility and user enhancements
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL
- Dark Theme


![demo (low res)](https://github.com/Uzay-G/archivy/raw/master/archivy.gif)


Upcoming:

- Links between different knowledge base items
- Multi User System.
- Option to compile data to a static site.

## Quickstart

Install with `pip install archivy` and then do `archivy run` to serve the app. You can open it at https://localhost:5000.

The first time you run archivy, an admin user will automatically be created with a random password.
These credentials will be printed to the log when you launch like this:

```
[2020-10-10 10:48:27,764] INFO in __init__: Archivy has created an admin user as it did not exist.
                            Username: 'admin', password: '5a512991c605ea51038ce2a0'
```

Login with these credentials and then you can change your password/username by clicking the profile button on the top left.

You can then use archivy to create notes, bookmarks and then organize and store information.
