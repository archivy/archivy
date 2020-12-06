
There are several ways you can edit content in Archivy.

Whenever you open a note or bookmark, at the bottom of the page you'll find a few buttons that allow you to edit it.


## Local Edit

You can do a **local edit**. This option is only viable if running archivy on your own computer. This will open the concerned file with the default app set to edit markdown.

For example like this:

![ex of local editing with marktext](img/local-edit.png)


This markdown file will be rendered following the [pandoc markdown spec](https://pandoc.org/MANUAL.html#pandocs-markdown). This includes mathematical equations, footnotes, and many other cool features.


## Through the app

If you're remotely hosting archivy, and you'd like to edit content, you can still do edits through the web app, by clicking "Toggle web editor" at the bottom.

Unfortunately this editor does not provide direct preview of math equations and other nice pandoc markdown features.

However, you can still use pandoc markdown syntax, save the changes, and render the dataobj through the normal archivy interface.
