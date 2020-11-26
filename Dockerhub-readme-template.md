# Archivy Container Image Documentation

![Docker Image Version (latest semver)](https://img.shields.io/docker/v/uzayg/archivy)
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/uzayg/archivy)
![Docker Pulls](https://img.shields.io/docker/pulls/uzayg/archivy)

![GitHub](https://img.shields.io/github/license/Uzay-G/archivy)
![GitHub contributors](https://img.shields.io/github/contributors/Uzay-G/archivy)
![GitHub Release Date](https://img.shields.io/github/release-date/Uzay-G/archivy)

![GitHub pull requests](https://img.shields.io/github/issues-pr/Uzay-G/archivy)
![GitHub stars](https://img.shields.io/github/stars/Uzay-G/archivy?style=social)


![PyPI](https://img.shields.io/pypi/v/archivy)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/archivy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/archivy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/archivy)


- [Quick Reference](#quick-reference)
- [Supported Tags And Respective `Dockerfile` Links](#supported-tags-and-respective-dockerfile-links)
  * [Supported Architectures](##supported-architectures)
  * [Description Of Tags](#description-of-tags)
    + [`latest`, `stable`, `<version>`](###latest-stable-<version>)
    + [`source`](###source)
    + [`prerelease`](###prerelease)
    + [`<commit-hash>`](###<commit-hash>)
    + [`untested-<version>`](###untested-<version>)
- [What Is Archivy](#what-is-archivy)
  * [Features](##features)
- [How To Use This Image](#how-to-use-this-image)
  * [Start An Archivy Instance](##start-an-archivy-instance)
  * [Running Container In Interactive Mode](##running-container-in-interactive-mode)
  * [Running Archivy CLI commands](##running-archivy-cli-commands)
  * [With Data Persistence](##with-data-persistence)
  * [Environment Variables](##environment-variables)
  * [Try Demo on *'Play With Docker'*](###try-demo-on-play-with-docker)
  * [Using Docker Compose](##using-docker-compose)
    + [Which Compose File To Use?](###which-compose-file-to-use)
  * [Running Archivy With Elasticsearch](##running-archivy-with-elasticsearch)
- [Container Security](#container-security)
  * [In `Dockerfile`](##in-dockerfile)
  * [Testing And Scanning](##testing-and-scanning)
  * [Image Usage](##image-usage)
    + [With `docker run`](###with-docker-run)
    + [With Docker Compose](###with-docker-compose)
- [Healthchecks](#healthchecks)
- [Image Variants](#image-variants)
  * [`archivy:<version>`, `archivy:stable`, `archivy:latest`, `archivy:master`, `archivy:prerelease`, `archivy:<commit-hash>`](##archivy:<version>-archivy:stable-archivy:latest-archivy:master-archivy:prerelease-archivy:<commit-hash>)
- [Packages Installed](#packages-installed)
  * [Installed By `requirements.txt`](##installed-by-requirements.txt)
  * [User-Installed Packages](##user-installed-packages)
    + [`xdg-utils`](###xdg-utils)
    + [`pandoc`](###pandoc)
- [Licence](#licence)

# Quick Reference

- Maintained by: [Uzay Girit](https://github.com/Uzay-G/archivy/tree/docker)

- Where to get help: [GitHub Project Page](https://github.com/Uzay-G/archivy), [Archivy Discord Server](https://discord.gg/uQsqyxB)  

- Where to file issues: [Project's GitHub Issues Page](https://github.com/Uzay-G/archivy/issues)
![GitHub issues](https://img.shields.io/github/issues/Uzay-G/archivy)

- Source of this description: [`docker` branch's `docs` directory](https://github.com/Uzay-G/archivy/tree/docker/docs)

# Supported Tags And Respective `Dockerfile` Links

- [`stable`, `latest`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.8.4`, `0.8.3`, `0.8.2`, `0.8.1`, `0.8.0`, `0.8`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.7.3`, `0.7.2`, `0.7.1`, `0.7.0`, `0.7`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.6.2`, `0.6.1`, `0.6.0`, `0.6`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.5.0`, `0.5`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.4.1`, 0.4`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.4.0`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.3.0`, `0.3`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.2.0`, `0.2`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`0.1.0`, `0.1`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile)
- [`source`](https://github.com/Uzay-G/archivy/blob/docker/Dockerfile.master)

The images are also tagged with their respective git commit hash. All tags are listed under `Tags` tab in DockerHub.

>**NOTE:**
>There are images that are tagged with the name `untested-`. **Do not** use these images. They are meant for testing purposes only.


## Supported Architectures

> **NOTE:**
> Versions of Archivy from `0.2.0` and higher require `pandoc` to function. As `pandoc` is not avaiable for most of the aforementioned architectures, it will be built only for `amd64` architecture.
> If you wish to use Archivy for other architectures, you will have to use version < `0.2.0`.

Archivy has been built for the following architectures with the help of `buildx`. This **does not** guarantee that the image will work as it should on all these architectures.

* `amd64`
* `arm64v8`
* `arm32v7`
* `arm32v6`
* `s390x`
* `i386`

`ppc64le` is not currently supported as Archivy does not build successfully on that architecture.

## Description Of Tags

### `latest`, `stable`, `<version>`
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/uzayg/archivy)

This is the de-facto image. If you are unsure about which image to use, you probably want to use the ones listed here. These images are built from Archivy's stable releases.

### `source`
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/uzayg/archivy/master)

This image is built from the `master` branch in GitHub. As such, the code in this branch *might* be ahead of the releases in terms of features and/or bug fixes.

### `prerelease`
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/uzayg/archivy/prerelease)

This image is built from the `prerelease` tags on GitHub. 

### `untested-<version>`

These images are **not meant to be used**. They exist for internal testing purposes only.

### `<commit-hash>`

Each image (except the ones with the `untested-` tag) are also tagged with the first 8 charaters of the commit hash. Look under the *Image Tags* section of Docker Hub, or check the image metadata for the value of the `VCS_REF` label.

>**NOTE:**
>
> All the aforementioned images are based on `python3.8-alpine` image, which is based on the [Alpine Linux Project](https://alpinelinux.org/). For more information, refer to the [Image Variants](#image-variants) section.

# What Is Archivy?

Archivy is a self-hosted knowledge repository that allows you to safely preserve useful content that contributes to your knowledge bank.

## Features

- If you add bookmarks, their webpages contents' will be saved to ensure that you will always have access to it, in sync with the idea of [digital preservation](https://jeffhuang.com/designed_to_last/).
- Allows you to sync up with Pocket to gather bookmarks from there too.
- Everything is a file! For ease of access and editing, all the content is stored in markdown files with yaml front matter.
- Extensible search with Elasticsearch and its Query DSL

# How To Use This Image

## Start An Archivy Instance

```shell
$ docker run -d --name archivy-test -p 5000:5000 uzayg/archivy
```

This will set up a basic instance of Archivy on your machine. Port `5000` has been connected to port `5000` on the container. In order to access the UI, open `http://localhost:5000` on your machine. If you wish to change the port of the host side, change the argument from `-p 5000:5000` to `-p [your-port]:5000`. This way, you can access Archivy at `http://localhost:[your-port]/`. This container runs in *detached* mode, meaning that no output is printed to the terminal. To view the logs, run

```shell
$ docker logs -f [name-of-container]
```

which will continuously stream the logs to the terminal. To exit, type ctrl+c. To just print the logs and exit, run the same command without the -f flag.

## Running container in interactive mode

You can also pass commands to the container by appending it to the docker run command. Keep in mind that the container will execute your commands and not run Archivy. This is useful if you want to find out what is going on inside the container. For example,

```shell
$ docker run -it --name archivy-test -p 5000:5000 uzayg/archivy sh
```

will start an interactive shell inside the container. Remember to pass the `-it` flags when you want access to a terminal inside the container.

>- `-i / --interactive` -- Keeps standard input open
>- `-t / --tty` -- Allocates a pseudo TTY

## Running Archivy CLI commands

You can pass arguments to the Archivy CLI by prefixing `archivy` to the command portion of the `docker run` command, similar to the [previous section](##running-container-in-interactive-mode).

The following command will run `archivy --version` in the container:
```sh
$ docker run --rm --name archivy-test -p 5000:5000 uzayg/archivy archivy --version
```

The following command will run `archivy routes` in the container:
```sh
$ docker run --rm --name archivy-test -p 5000:5000 uzayg/archivy archivy routes
```

The following command will run `archivy shell` in the container:
```sh
$ docker run -it --name archivy-test -p 5000:5000 uzayg/archivy archivy shell
```
> _NOTE_:
> Do not forget to add the `-it` flags when you need access to an interactive terminal, as shown above. Else, the container will exit right after running the command.

> **NOTE**:
> Keep in mind that for all arguments except `shell`(`archivy shell`), will result in the container terminating after the command has been run. To get access to an interactive shell inside the container, refer to the [previous section](##running-container-in-interactive-mode).

## With Data Persistence

You can bind-mount any directory on your host to the data directory on the container in order to ensure that if and when the container is stopped/terminated, the data saved to the container isn’t lost. This can be done as follows:

```shell
docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/archivy/data uzayg/archivy
```

> `-v / --volume host:container`	——	Bind-mount host path to container path

The argument `-v /path/to/host/dir:/archivy/data` bind-mounts the directory `/path/to/host/dir` on the host to `/archivy/data` on the container.

If you wish to mount, say `/home/bob/data`, you would first need to create the data directory at `/home/bob`, and then change the argument to `-v /home/bob/data:/archivy/data`.

This container is configured to use `/archivy/data` as the location where all data will be saved. You can bind-mount a host directory to this location as shown above.

## Environment Variables

You can inject environment variables while starting the container as follows:

```shell
$ docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/archivy/data -e FLASK_DEBUG=1 -e ELASTICSEARCH_ENABLED=0 -e ELASTICSEARCH_URL="http://localhost:9200/" uzayg/archivy
```

>`-e/--env KEY=value`	——	Set the environment variable(key=value)

Multiple such environment variables can be specified during run time. For now, Archivy supports the following environment variables

| ENVIRONMENT VARIABLE | DEFAULT | DESCRIPTION |
|:--------------------:|:-------:|-------------|
| `FLASK_DEBUG` | `0` | Runs Flask in debug mode if value is `1`. More verbose output to console. |
| `ELASTICSEARCH_ENABLED` | `0` | Enables Elasticsearch support if value is `1`. |
| `ELASTICSEARCH_URL` | `http://localhost:9200/` | Sets the URL at which Elasticsearch listens. |
| `ARCHIVY_DATA_DIR` | On Linux systems, it follows the [XDG specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html): `~/.local/share/archivy` | Directory in which data will be saved |
| `ARCHIVY_PORT` | `5000` | Port number on which Archivy listens. |

---

> **NOTE**:
>
> The environment variable `ARCHIVY_DATA_DIR` is already set to `/archivy/data` by the container image. This cannot be changed by the user unless they build the image from scratch.
>
> The environment variable `ARCHIVY_PORT` is already set to `5000` by the container image. This cannot be changed by the user unless they build the image from scratch, in which case they will also need to change the port in the `Dockerfile`.

If the values are not set by the user, they are assigned default values during run time.

> **NOTE**:
> 
> If you wish to use Archivy with Elasticsearch, read on. The setup is explained in the **Docker Compose** section below.


## Try Demo on *'Play With Docker'*

For those with DockerHub accounts, you can try a version of Archivy on Play With Docker by clicking on the badge below. This will require you to log in to your DockerHub account.

[![Try in ‘Play With Docker’](https://github.com/play-with-docker/stacks/raw/cff22438cb4195ace27f9b15784bbb497047afa7/assets/images/button.png)](https://labs.play-with-docker.com/?stack=https://raw.githubusercontent.com/Uzay-G/archivy/docker-compose.yml)

This instance of Archivy is based on the following Docker Compose file:

```yaml
version: '3.8'
services:
  archivy:
    image: uzayg/archivy
    ports:
      - "5000:5000"
    volumes:
      - archivyData:/archivy/data
    environment:
      - FLASK_DEBUG=0
      - ELASTICSEARCH_ENABLED=0
      
volumes:
  archivyData:
```

>**NOTE**:
>
>As is visible from the above compose file, this is a version of Archivy running without Elasticsearch enabled. Therefore, the search function will not work.

## Using Docker Compose

Docker Compose is an easier way to bring up containers when compared to running lengthy docker run commands. The `docker-compose.yaml` file contains all the necessary information that you would normally provide to the `docker run` command, declared in a YAML format. Once this file is written, it as simple as running the following command in the same directory as the `docker-compose.yml` file:

```shell
$ docker-compose up -d
```

This works as long as the compose file is named `docker-compose.yml`. If it has a different name, you will need to specify the path to the file as an argument to the `-f` flag as shown below:

```shell
$ docker-compose -f ./compose.yml up -d
```

This repository contains two compose files(for now). A version of the simpler one is given below:

```yaml
version: '3.8'
services:
  archivy:
    image: uzayg/archivy
    ports:
      - "5000:5000"
    volumes:
      - archivyData:/archivy/data
    environment:
    	- FLASK_DEBUG=1
    	- ELASTICSEARCH_ENABLED=0
    drop_cap:
      - ALL
    	
volumes:
  archivyData:
```

This file

- pulls the container image uzayg/archivy from DockerHub.
- binds port `5000` on the host to port `5000` on the container.
- creates a named volume `archivyData` on the host and mounts it to the `/archivy/data` directory on the container(which is where all persistent data will be stored).
- Sets the following environment variables so that they can be used by Archivy during run time
  * `FLASK_DEBUG=1`
  * `ELASTICSEARCH_ENABLED=0`
- Drops all privileged capabilities for the container.

This would be the same as running the following commands:

```shell
$ docker volume create archivyData
$ docker run -d -p 5000:5000 -v archivyData:/archivy/data --cap-drop=ALL -e FLASK_DEBUG=1 -e ELASTICSEARCH_ENABLED=0 uzayg/archivy
```
When multiple container get involved, it becomes a lot easier to deal with compose files.

### Which Compose File To Use?

There are currently two compose files in the repository:

- `docker-compose.yml`
- `docker-compose-with-elasticsearch.yml`

If you would like to test Archivy, just download the `docker-compose.yml` and run the following command from the same directory in which `docker-compose.yml` is present.

```shell
$ docker-compose up -d
```

The contents of the file are shown below:

```yaml
version: '3.8'

services:
  archivy:
    image: uzayg/archivy
    ports:
      - "5000:5000"
    volumes:
      - archivyData:/archivy/data
    environment:
    	- FLASK_DEBUG=0
    	- ELASTICSEARCH_ENABLED=0
    cap_drop:
      - ALL
    	
volumes:
  archivyData:
```

This file

- pulls the official `archivy` image.
- binds port `5000` on the host to port `5000` on the container.
- creates a named volume `archivyData` on the host and mounts it to the `/archivy/data` directory on the container(which is where all persistent data will be stored).
- Drops all privileged capabilities for the container(better for security).

> **NOTE**:
>
> If you wish to bind-mount a folder to Archivy, modify `volumes` as shown below:
>
> ```yaml
>services:
>  archivy:
>     ...
>     volumes:
>       - ./archivyData:/archivy/data
> ```
> This will create a folder named archivyData in your current working directory. This is the folder in which all user-generated notes/bookmarks will be stored.

If you wish to test Archivy’s full capabilities with Elasticsearch, use the `docker-compose-with-elasticsearch.yml`. The usage of this file is explained in the next section.

## Running Archivy With Elasticsearch

The compose file given below will do the following:

- Set up an instance/container of Elasticsearch that listens on port `9200`.
- Set up an instance/container of Archivy that listens on port `5000`.
- Ensure that the two can communicate with each by setting the appropriate environment variables(`ELASTICSEARCH_ENABLED` and `ELASTICSEARCH_URL`).
- Both containers have volumes attached to them to ensure data persistence.
- The users and processes in the containers are run with only as much privileges as necessary. All other capabilities are dropped, and necessary capabilities are explicitly mentioned.

```yaml
version: '3.8'
services:

  archivy:
    image: uzayg/archivy
    ports:
      - target: 5000
        published: 5000
        protocol: tcp
    volumes:
      - archivyData:/archivy/data
    environment:
      - FLASK_DEBUG=0
      - ELASTICSEARCH_ENABLED=1
      - ELASTICSEARCH_URL=http://search:9200/
    networks:
      - archivy
    depends_on:
      - elasticsearch
    cap_drop:
      - ALL
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
  
  elasticsearch:
    image: elasticsearch:7.9.0
    ports:
      - target: 9200
        published: 9200
        protocol: tcp
    volumes:
      - searchData:/usr/share/elasticsearch/data
    environment:
      - "discovery.type=single-node"
    networks:
      archivy:
        aliases:
          - search
    cap_drop:
      - ALL
    cap_add:
      - SYS_CHROOT
      - SETUID
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3

networks:
  archivy:

volumes:
  archivyData:
  searchData:
```
For a detailed description of the declarations used in the compose file, refer to the [official documentation](https://docs.docker.com/compose/compose-file/#networks).

Given below is a simplified version of the same compose file which should be fine for testing purposes:

```yaml
version: '3.8'
services:

  archivy:
    image: uzayg/archivy
    ports:
    	- "5000:5000"
    volumes:
      - ./archivyData:/archivy/data
    environment:
      - FLASK_DEBUG=0
      - ELASTICSEARCH_ENABLED=1
      - ELASTICSEARCH_URL=http://elasticsearch:9200/
    depends_on:
      - elasticsearch
  
  elasticsearch:
    image: elasticsearch:7.9.0
    ports:
      - "9200:9200"
    volumes:
      - ./searchData:/usr/share/elasticsearch/data
    environment:
      - "discovery.type=single-node"
```

The declarations are described below:

- For the `archivy` service (`archivy:`)
  * Pulls the `uzayg:archivy` image. (`image:`)
  * Connects port `5000` on the host to port `5000` on the container. (`ports:`)
  * Creates the `archivyData` directory in the current working directory and bind-mounts it to the `/archivy/data` directory in the `archivy` container. (`volumes:`)
  * Sets the following environment variables. (`environment:`)
    + `FLASK_DEBUG=0`
    + `ELASTICSEARCH_ENABLED=1` *(required to enable Elasticsearch support)*
    + `ELASTICSEARCH_URL=http://elasticsearch:9200/` *(required by Archivy to connect to Elasticsearch)*
  * Sets a condition that the `archivy` container will start only after the `elasticsearch` container starts. (`depends_on:`)
- For the `elasticsearch` service
  * Pulls the `elasticsearch:7.9.0` image. (`image:`)
  * Connects port `9200` on the host to port `9200` on the container.
  * Creates the `searchData` directory on the host in the current working directory and bind-mounts it to the `/usr/share/elasticsearch/data` directory in the `elasticsearch` container.(`volumes:`)
  * Sets the following environment variable
    + `discovery.type=single-node` *(Required if a single instance of Elasticsearch is to be run.)*

# Container Security

Given below are the measures that have been taken to ensure that the container image adheres to the best practices concerning image security.
Some suggestions have also been listed regarding usage of this image.

## In `Dockerfile`

- The `archivy` process is run as a non-root, unprivileged user(by the same name) inside the container. The non-root user is created with the following settings:
  * User : `archivy`
    + UID : `1000`
  * Group : `archivy`
    + GID : `1000`
  * Shell : `/sbin/nologin`
  * Home Directory : `/archivy`
  * System account
  * Login disabled
- All directories that `archivy` process needs to write to are owned by the `archivy` user.
- In `docker-compose-with-elasticsearch.yml`
  * all capabilities have been dropped in the `archivy` container. This ensures that privileged actions such as binding to ports, making ping requests and the like are denied.
  * first, all capabilities have been droppped in the `elasticsearch` container. Then, only the following capabilities have been granted(as they are required for Elasticsearch to start and run):
    + `SYS_CHROOT`
      - Use `chroot(2)`, change root directory
    + `SETUID`
      - Make arbitrary manipulations of process UIDs.
- Except the following packages, no others are installed on the image:
  * `xdg-utils` - Required by Archivy to open files for editing using the `xdg-open` command.
  * `pandoc` - Required by Archivy for extended Markdown support and conversion between file formats.

## Testing And Scanning

Each time the container is built, it is tested using
* [Hadolint](https://github.com/hadolint/hadolint)
* [Container Structure Test](https://github.com/GoogleContainerTools/container-structure-test)

and scanned for vulnerabilities using
* [Aqua Security's Trivy](https://github.com/aquasecurity/trivy)
* [Anchore Scan](https://github.com/anchore/scan-action)
* [Synk](https://github.com/snyk/snyk) *(Not yet implemented. Will be added soon.)*

and if there are any vulnerabilities with a severity of greater than or equal to `HIGH` for which a fix exists, the build fails and the container is not pushed to Docker Hub. 

The build pipeline does the following:

* Lints the `Dockerfile` using [Hadolint](https://github.com/hadolint/hadolint) in order to avoid bad practices and errors.
* Builds the image and pushes it to DockerHub with the `untested-` tag.
* Tests the image with the `untested-` tag using [Container Structure Test](https://github.com/GoogleContainerTools/container-structure-test) which is a testing tool that checks the container against user-defined tests. For Archivy, the following checks/tests are done.
  - checks if all the metadata set is correct.
  - checks if all necessary files/folders exist.
    + checks if those files/folders have the right permissions and ownership.
  - checks if the user running within the container is an unprivileged user.
  - checks if the right ports are exposed.
  - checks if the right volume is set.
  - checks if the right `ENTRYPOINT` and `CMD` values are set.
* Scans the image for vulnerabilities using [Aqua Security's Trivy](https://github.com/aquasecurity/trivy).
  - If the image contains any vulnerabilities of severity `CRITICAL,HIGH` for which a fix exists, the build fails.
* Scans the image using [Anchore Scan](https://github.com/anchore/scan-action).
* Once all checks have passed, the final image is built and pushed with the appropriate tags to DockerHub.


## Image Usage

Given below are a few suggestions based on how you wish to use the image.

### With `docker run`

If you're running the container using `docker run` commands, it is suggested that for
* `archivy`, add the flag
  - `--cap-drop=ALL`
```shell
$ docker run -d --name archivy-test -p 5000:5000 --cap-drop=ALL uzayg:archivy
```
and for 
* `elasticsearch`, add the following flags
  - `--cap-drop=ALL`
  - `--cap-add=SYS_CHROOT`
  - `--cap-add=SETUID`
```shell
$ docker run -d --name elasticsearch-test -p 9200:9200 --cap-drop=ALL --cap-add=SYS_CHROOT --cap-add=SETUID --env "discovery.type=single-node" elasticsearch:7.9.0
```

### With Docker Compose

If you're launching the containers using Docker Compose, use the compose files present in the [repository's `docker` branch](https://github.com/Uzay-G/archivy/tree/docker).

If you wish to run *just* Archivy, use the `docker-compose.yml` file, and if you wish to run both Archivy *and* Elasticsearch, use the `docker-compose-with-elasticsearch.yml` file.

Both files have been configured to run the containers with dropped capabilties as shown in the [previous section](#with-docker-run).

# Healthchecks

This image implements the `HEALTHCHECK` directive in the `Dockerfile` in order to ensure that Archivy is up and running before routing traffic to the container. This is done by the Docker daemon automatically when the `HEALTHCHECK` directive is specified.

The HEALTHCHECK command used is

```Dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=5 CMD healthcheck.sh
```
which does the following:

* Initially waits for `30` seconds (container is in `starting` state.)
* Waits for `5` more seconds before running the script `healthcheck.sh` (container is in `starting` state.)
* Runs the `healthcheck.sh` script. If it succeeds, the container is tagged as `healthy`. Else
  - Waits for `5` seconds before declaring a timeout.
  - Tries for a maximum of 5 times if the healthcheck fails after which the container is tagged as `unhealthy`.
* Checks the container every `30` seconds using the `healthcheck.sh` script.

Given below is the script that is used to perform the health check on Archivy:

```sh
#!/usr/bin/env sh
#
#: Title        : healthcheck.sh
#: Date         : 02-Sep-2020
#: Version      : 0.2
#: Description  : The script check the running status of Archivy.
#                 The exit status of this script decides whether
#                 or not the container is reported as 'healthy'
#                 by the Docker daemon.
#                 
#: Options      : None required. This will be run by Docker.
#: Usage        : Run the script `./healthcheck.sh`. In this case,
#                 pass the script as an argument to the HEALTHCHECK
#                 command in the Dockerfile as shown below
#
#                   HEALTHCHECK CMD /path/to/healthcheck.sh
################


# Function used to check if Archivy is up and running.
# If it is running, the function returns a 0, else 1.
#
# Function input    :  Accepts none.
#
# Function output   :  Returns 0 if archivy is up and running.
#                      Returns 1 if it is not.
#
checkArchivy() {
  # Local variables used to store hostname and port number of Archivy
  archivyHostname="localhost"
  archivyPort="5000"

  # If 'wget' command is available
  if [ $(command -v wget) ] ; then
    # Get the home page of Archivy
    archivyRunning="$(wget -qO- http://${archivyHostname:-"localhost"}:${archivyPort:-"5000"}/ 2>/dev/null | grep -oE "Archivy|New Bookmark|New Note")"
  elif [ $(command -v curl) ] ; then
    archivyRunning="$(curl -X GET http://${archivyHostname:-"localhost"}:${archivyPort:-"5000"}/ 2>/dev/null | grep -oE "Archivy|New Bookmark|New Note")"
  else
    printf '%s\n' "Please install either wget or curl. Required for health checks on Elasticsearch." 1>&2
    exit 1
  fi

  # If the query result is not an empty string
  if [ "$( echo "${archivyRunning}" )" != "" ] ; then
    exit 0
  else
    exit 1
  fi
}


# Function that performs a health check on Archivy.
#
# Function input    :   None
#
# Function output   :   None
#
# Main function
main() {
  # Calling the 'checkArchivy' function
  checkArchivy || exit 1
}


# Calling the main function
main

# End of script
```

# Image Variants

The `archivy` image currently comes in one variant/flavour which is based on Alpine Linux.

## `archivy:<version>`, `archivy:stable`, `archivy:latest`, `archivy:master`, `archivy:prerelease`, `archivy:<commit-hash>`

The images with these tags are built on top of [`python3.9-alpine`](https://github.com/docker-library/python/blob/c99c77547e99f80fb9b895b7dc13b88b78170e2e/3.9/alpine3.12/Dockerfile) image which is Python3.8 installed on Alpine Linux `3.12`. There are no additional packages installed *except* for Archivy and the packages it requires.

The following can change on a later date, if necessary
* Version of Python
* Version of Alpine Linux

For a list of all packages installed in the image, refer to the [Packages Installed](#packages-installed) section.

# Packages Installed

## Installed by `requirements.txt`

%requirements%

## User-Installed Packages

### `xdg-utils`

Contains the binary `xdg-open` which is required by Archivy. This will be removed from this container on a later date. Currently, when creating a note within Archivy, it tries to open the file on the host, which it does using `xdg-open`.

```
xgd-utils1.1.3-r0 description:
Basic desktop integration functions

xgd-utils1.1.3-r0 webpage:
https://portland.freedesktop.org/wiki

xgd-utils1.1.3-r0 installed size:
292 kB

xgd-utils1.1.3-r0 license:
MIT
```

### `pandoc`

Contains the `pandoc` binary which is required by Archivy.

```
pandoc2.9.2.1-r0 description:
universal markup converter

pandoc2.9.2.1-r0 webpage:
https://pandoc.org/

pandoc2.9.2.1-r0 installed size:
66.54 MB

pandoc2.9.2.1-r0  license:
GPL-2.0-or-later
```

# Licence

This project is licensed under the MIT License - see the [LICENSE file](https://raw.githubusercontent.com/Uzay-G/archivy/master/LICENSE) for details. 

As with all Docker images, these likely also contain other software which may be under other licenses (such as Bash, etc from the base distribution, along with any direct or indirect dependencies of the primary software being contained).

As for any pre-built image usage, it is the image user's responsibility to ensure that any use of this image complies with any relevant licenses for all software contained within.
