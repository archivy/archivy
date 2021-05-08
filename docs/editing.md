## Format

Archivy files are in the [markdown](https://daringfireball.net/projects/markdown/basics) format following the [commonmark spec](https://spec.commonmark.org/).

We've also included a few powerful extensions:

- **Bidirectional links**: You can create a link to a note by clicking the "Link to a note" button. All links to a given note will be displayed when you visit that note, at the bottom in the "Backlinks" section.

- **In-editor bookmarking**: if you'd like to store a local copy of a webpage you're referring to inside an archivy note, simply select the url and click the "bookmark" icon.

- **LaTeX**: you can render mathematical expressions like this:

```md
$$
\pi = 3.14
$$
```

- **Footnotes**:
	```md
	What does this describe? [^1]

	[^1]: test foot note.
	```

- **Tables**:
	```md
	| Column 1 | Column 2 |
	| -------- | -------- |
	| ...      | ...      |
	```

- **Code blocks with syntax highlighting**:
	````md
	```python
	print("this will be highlighted")
	x = 1337
	```
	````

There are several ways you can edit content in Archivy.

Whenever you open a note or bookmark, at the bottom of the page you'll find a few buttons that allow you to edit it.

## Editing through the web interface

You can edit through the web app, by clicking "Toggle web editor" at the bottom. This is the recommended way because the Archivy web editor provides useful functionality. You can save your work, link to other notes with the "Link to a note button", and archive webpages referenced in your note, all inside the editor!

## Locally

You can do a **local edit**. This option is only viable if running archivy on your own computer. This will open the concerned file with the default app set to edit markdown.

For example like this:

![ex of local editing with marktext](img/local-edit.png)
