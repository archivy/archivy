# Archivy

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

Features:


- If you add bookmarks, their webpages contents' will be saved to ensure that you will **always** have access to it, in sync with the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Allows you to sync up with Pocket to gather bookmarks from there too.
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL


![demo (low res)](https://github.com/Uzay-G/archivy/raw/master/archivy.gif)
Upcoming:

- Integrations with HN, Reddit, and many more.
- Add submodules for digital identity so archivy syncs to your hn upvoted posts, reddit saved, etc...
- Option to compile data to a static site that can be deployed.

## Setup

### Local Setup

- Make sure your system has Python installed.
- Clone the repository.
- `cd` into the project directory.
- create a virtual env by running `python3 -m venv venv/`.
- run `pip install -r requirements.txt` or `pip3`.
- execute the `start.sh` script
- see below for setting up search functionality


### With Docker

- Make sure that your system has Docker installed. You can check if it is installed by running
```
$ docker --version
Docker version 19.03.12, build 48a66213fe
```

If you wish to test the image for yourself, you can run
```
docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/usr/src/app/data harshavardhanj/archivy:latest
```
and you can access the service at `http://localhost:5000/` on your browser.

- The argument `-p 5000:5000` bind port 5000 on the host to port 5000 on the container. If you wish to access the server at `http://localhost:9000/` instead, you would change the argument to `-p 9000:5000`.

- The argument `-v /path/to/host/dir:/usr/src/app/data` bind-mounts the directory `/path/to/host/dir` on the host to `/usr/src/app/data` on the container. If you wish to mount, say `/home/bob/data`, you would first need to create the `data` directory at `/home/bob`.


There are *two* Dockerfiles in the repository. 

#### `local-build.Dockerfile`

This is geared towards people who prefer to clone the repository, make changes to it locally, and built the container image. This Dockerfile does not fetch/clone the repository into the container. It copies all files in the current context(current working directory) into the container. Therefore, this file will **need** to be present in the root of the repository for it to build successfully.


#### `Dockerfile`

For people who don't wish to clone the repository and want to just build/test the image on their own, the file named `Dockerfile` will be sufficient. This file fetches a copy of the repository each time the image is built. While this is more portable than the `local-build.Dockerfile`, it isn't efficient for local development as you would be pulling a copy of the repository each time you built the image.

#### Docker Compose

There are *two* compose files present in the repository which can be used instead of the long `docker run` commands previously mentioned. The container(s) can be brought up with a `docker-compose up -d -f ./docker-compose.yaml`.

##### `docker-compose.yaml`

The contents of the file are pasted below, and a brief description of the options in the file is given below:

`$ cat docker-compose.yaml`
```yaml
# Docker Compose file for Archivy
version: "3.8"
services:
  archivy:
    image: harshavardhanj/archivy
    ports:
      - "5000:5000"
    volumes:
      - ./data:/usr/src/app/data
```

This file 
- pulls the container image `harshavardhanj/archivy`
- binds port `5000` on the host to port `5000` on the container
- creates a directory `data` in the current working directory on the host and bind-mounts it to the `/usr/src/app/data` directory on the container(which is where all persistent data will be stored).

##### `docker-compose-local-build.yaml`

The contents of the file are pasted below, and a brief description of the options in the file is given below:

`$ cat docker-compose-local-build.yaml`
```yaml
# Docker Compose file for Archivy
# Use this if you wish to build the image on your own
version: "3.8"
services:
  archivy:
    build:
      context: .
      dockerfile: local-build.Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - ./data:/usr/src/app/data

```

This compose file will look for a Dockerfile from which to build the container image, which will then be run. Just like with the `local-build.Dockerfile`, this compose file needs to be present in the root of the repository for it to run. The options are described below:

This file
- builds an image with the current context(with all files present in the current working directory) and the `local-build.Dockerfile` Dockerfile
- binds port `5000` on the host to port `5000` on the container
- creates a directory `data` in the current working directory on the host and bind-mounts it to the `/usr/src/app/data` directory on the container(which is where all persistent data will be stored)


> NOTE:
> If you don't want to clone the whole repository to use the above compose file, just replace `local-build.Dockerfile` with `Dockerfile`. As long as you have the `Dockerfile` file present, you can build and run the container.
> ```yaml
>services:
>  archivy:
>    build:
>      context: .
>      dockerfile: Dockerfile
>```
> Make sure that you have `Dockerfile` in the same directory as the compose file.



### Setting up Search

Archivy uses [ElasticSearch](https://www.elastic.co) to provide efficient full-text search.

Add these lines to your flaskenv:

```bash
ELASTICSEARCH_ENABLED=1
ELASTICSEARCH_URL=http://localhost:9200
```

Instructions to install and run the service are provided [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html).


Append these two lines to your [elasticsearch.yml config file](https://www.elastic.co/guide/en/elasticsearch/reference/current/settings.html):

```yaml
http.cors.enabled: true
http.cors.allow-origin: "http://localhost:5000"
```
