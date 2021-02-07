
This document is a general overview of how the different pieces of archivy interact and what technologies it uses. Reading this will be useful for people looking to access the inner archivy API to write plugins. Read [this post](https://www.uzpg.me/tech/2020/07/21/architecture-md.html) to understand what the function of an `architecture.md` file is.


Archivy is:

- A [Flask](https://flask.palletsprojects.com/) web application.
- A [click](https://click.palletsprojects.com/) backend command line interface.


You use the cli to run the app, and you'll probably be using the web application for direct usage of archivy.


## Data Storage

- `DataObjs` is the term used to denote a note or bookmark that is stored in your knowledge base (abbreviation for Data Object). These are stored in a directory on your filesystem of which you can [configure the location](../config.md). They are organized in markdown files with `yaml` front matter like this:

```yaml
---
date: 08-31-20
desc: ''
id: 100
path: ''
tags: []
title: ...
type: note
---

...
```

Archivy uses the [python-frontmatter](https://python-frontmatter.readthedocs.io/en/latest/) package to handle the parsing of these files. They can be organized into user-specified sub-directories. Check out [the reference](filesystem_layer.md) to see the methods archivy uses for this.

- Another storage method Archivy uses is [TinyDB](https://tinydb.readthedocs.io/en/stable/). This is a small, simple document-oriented database archivy gives you access to for persistent data you might want to store in archivy plugins. Use [`helpers.get_db`](/reference/helpers/#archivy.helpers.get_db) to call the database.

## Search

Archivy uses [Elasticsearch](https://www.elastic.co/) to index and allow users to have full-text search on their knowledge bases. 

Elasticsearch requires configuration to have higher quality search results. You can check out the top-notch config archivy already uses by default [here](https://github.com/archivy/archivy/blob/master/archivy/config.py).

Check out the [helper methods](search.md) archivy exposes for ES.

## Auth

Archivy uses [flask-login](https://flask-login.readthedocs.io/en/latest/) for auth. All endpoints require to be authenticated. You can create an admin user with the `create-admin` command.

In our roadmap we plan to extend our permission framework to have a multi-user system, and define configuration for the permissions of non-logged in users. In general we want to make things more flexible on the auth side.


## How bookmarks work

One of the core features of archivy is being able to save webpages locally. The way this works is the conversion of the html of the page you specify to a simple, markdown file.

We might want to extend this to also be able to save PDF, EPUB and other formats. You can find the reference for this part [here](models.md).

Further down the road, it'd be nice to add background processing and not only download the webpage, but also save the essential assets it loads for a more complete process. This feature of preserving web content aligns with the mission against [link rot](https://en.wikipedia.org/wiki/Link_rot) [^1].

## Plugins

Plugins in archivy function as standalone python packages. The phenomenal [click-plugins](https://github.com/click-contrib/click-plugins) package allows us to do this by basically adding commands to the cli. 

So you create a python package where you specify commands to extend your pre-existing archivy cli. Then these added commands will be able to be used through the cli. But what makes plugins interesting is that you can actually also use the plugins through the web interface, without having access to the system running archivy. We use an adaptation of the [click-web](https://github.com/fredrik-corneliusson/click-web) to convert your cli commands to interactive web forms.


[^1]: See [this manifesto](https://jeffhuang.com/designed_to_last/) to learn more about this phenomenon.
