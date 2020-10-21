

# API documentation

The archivy api allows you to interact with your archivy instance through HTTP. This allows a complete, programmatic access to the archivy's functionality.

All these requests must be made by an authenticated user. For example, using the python `requests` module:

```python
import requests
# we create a new session that will allow us to login once
s = requests.session()

INSTANCE_URL = <your instance url>
s.post(f"{INSTANCE_URL}/api/login", auth=(<username>, <password>))

# once you've logged in - you can make authenticated requests to the api, like:
resp = s.get(f"{INSTANCE_URL}/api/dataobjs").content)
```

## API spec
This is an api specification for the routes you might find useful in your scripts. The url prefix for all the requests is `/api`.

### General routes

| Route name    | Parameters                                                   | Description                                          |
| ------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| POST `/login` | [HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication): username and password | Logs you in with your archivy username and password  |
| GET `/search` | `query`: search query                                        | Fetches elasticsearch results for your search terms. |



### Folders

| Route name               | Parameters                                                   | Description                                                  |
| ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| POST `/folders/new`      | `path`: path of new directory For example, if you want to create the directory `trees` in the existing directory `nature`, `path = "nature/trees"` | Allows you to create new directories                         |
| DELETE `/folders/delete` | `path`: path of directory to delete. For example, if you want to delete the `trees` dir in `nature`, `path = natures/trees` | Deletes existing directories. Also works if the directories contain data, which will be deleted with it. |

### Dataobjs

| Route name            | Parameters                                                   | Description                                                  |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| POST `/notes`         | `title`, `content`, `desc`, `tags`: array of tags to associate with the note, `path`: string with the relative dir in which the note should be stored. | Creates a new note in the knowledge base. The only required parameter is the title of the note. |
| POST `/bookmarks`     | `url`, `desc`, `tags`: array of tags to associate with the bookmark, `path`: string with the relative dir in which the note should be stored. | Stores a new bookmark. Only required parameter is `url`.     |
| GET `/dataobjs`       |                                                              | Returns an array of all dataobjs with their title, id, contents, url, path etc... This request is resource-heavy so we might need to consider not sending the large contents. |
| GET `/dataobjs/id`    |                                                              | Returns data for **one** dataobj, specified by his id.       |
| DELETE `/dataobjs/id` |                                                              | Deletes specified dataobj.                                   |

