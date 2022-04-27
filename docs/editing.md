Note: to enable auto save in the editor, see [this](https://archivy.github.io/config/#editor-configuration).

## Format

Archivy files are in the [markdown](https://daringfireball.net/projects/markdown/basics) format following the [commonmark spec](https://spec.commonmark.org/).

We've also included a few powerful extensions:

- **Bidirectional links**: You can easily link to a new note in the web editor by typing `[[`: an input box will appear where you can enter the title of the note you want to link to. Otherwise, links between notes are in the format `[[linked note title|linked note id]]`. If the title you wrote doesn't refer to an existing note, you can click enter and Archivy will create a new note.

- **Embedded tags**: You can directly add tags inside your notes with this `#tag#` syntax (see below). These tags and their groupings can then be viewed by clicking `Tags` on the navigation bar. Starting to type `#` in the web editor will display an input where you can search existing tags.

```md
I was going to a #python# conference, when I saw a #lion#.
```

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
