# Guide to using Archivy with Docker

This document contains enough information to help you get started with using Archivy as
a container, in this case, with Docker(although you can use any other container runtime).

This document will cover the following:

- [x] [Building a container image of Archivy](#building-archivy)
- [x] [Running Archivy as a container](#running-archivy)
  - [x] [Quick start](#quick-start)
  - [x] [Running Archivy along with persistent data storage](#with-data-persistence)
  - [x] [Running Archivy with environment variable injection](#environment-variable-injection)
  - [x] [Demo on ‘*Play With Docker*’](#try-demo-on-play-with-docker)
  - [x] [Running Archivy using Docker Compose](#using-docker-compose)
    - [x] [Running Archivy with Elasticsearch for full text search capabilities(with Docker Compose)](#running-archivy-with-elasticsearch)

Planned for the future:

- [ ] [Running Archivy using Docker Swarm(container orchestrator)](#using-docker-swarm)
- [ ] [Running Archivy on Kubernetes as a production-ready setup](#using-kubernetes)
- [ ] [Running Archivy on OpenStack as a production-ready setup(will be done only **after** the aforementioned points are completed)](#using-openstack)



> **NOTE**:
> Parts of the document may be incomplete as it is a work in progress. In time, more information will be added to each section/topic. If some part of the documentation is ambiguous, feel free to ask questions or make suggestions on the Issues page of the project. If necessary, additional revisions to the documentation can be made based on user feedback.



## Prerequisites

* Docker needs to be installed.

You can check if Docker is installed by running

```sh
$ docker --version
Docker version 19.03.12, build 48a66213fe
```

If you don't have Docker installed, take a look at the [official installation guide](https://docs.docker.com/get-docker/) for your device.



## Building Archivy

### Building using `Dockerfile`

The file `Dockerfile` is much more portable than the `local-build.Dockerfile` as you do not need any other additional files to build the image. The Dockerfile automatically downloads the source code during the build stage. Just download `Dockerfile` and run the following command to build the image:

```shell
$ docker build -t archivy:1.0 -f /path/to/Dockerfile .
```
This tags the image with the name `archivy:1.0`. Technically, you do not need to mention the path to `Dockerfile` as long as the Dockerfile is titled `Dockerfile`. If the name is anything but that, you will need to mention the path using the `-f` flag. So the above command is the same as

```sh
$ docker build -t archivy:1.0 .
```

There's an easier way to build the image. You can pass the URL to the GitHub repository directly to `docker`, and as long as there’s a file named `Dockerfile` in the root of the repository, Docker will build it.

```sh
$ docker build -t archivy:1.0 https://github.com/Uzay-G/archivy.git#docker
```
This will clone the GitHub repository and use the cloned repository as context. The Dockerfile at the root of the repository is used as `Dockerfile`.

> **NOTE**:
>
> The `master` branch of the Archivy repository does **not** contain any Dockerfiles. All files pertaining to Docker are available in the `docker` branch of this repository.



## Running Archivy

### Quick Start

You can get an instance of Archivy up and running for testing purposes with the following one-liner:

```sh
$ docker run -d --name archivy-test -p 5000:5000 harshavardhanj/archivy
```

> `--name`													——		Name of the container(can be anything)
>
> `-p/--publish host:container`		  ——		Bind port on host to port on container

The above command runs a container with the name `archivy-test` and binds port `5000` on the host to port `5000` on the container. That way, you can access the server at `http://localhost:5000/` on the device. If you wish to access the server at `http://localhost:9000/` instead, you would change the argument to `-p 9000:5000`. This container runs in *detached* mode, meaning that no output is printed to the terminal. To view the logs, run

```sh
$ docker logs -f [name-of-container]
```

which will continuously stream the logs to the terminal. To exit, type `ctrl+c`. To just print the logs and exit, run the same command without the `-f` flag.

> **NOTE**:
>
> There’s an image available on DockerHub for testing purposes. It is titled `archivy` and is available in the `harshavardhanj` repository on DockerHub. You can pull the image using 
>
> ```shell
> $ docker pull harshavardhanj/archivy
> ```



#### Running container in interactive mode

You can also pass commands to the container by appending it to the `docker run` command. Keep in mind that the container will execute your commands and **not run** Archivy. This is useful if you want to find out what is going on inside the container. For example,

```sh
$ docker run -it --name archivy-test -p 5000:5000 harshavardhanj/archivy sh
```

will start an interactive shell inside the container. Remember to pass the `-it` flags when you want access to a terminal inside the container. 

- `-i/--interactive` — Keeps standard input open
- `-t/--tty` — Allocates a pseudo TTY



### With Data Persistence

You can bind-mount any directory on your host to the data directory on the container in order to ensure that if and when the container is stopped/terminated, the data saved to the container isn’t lost. This can be done as follows:

```shell
$ docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/archivy/data harshavardhanj/archivy
```

> `-v/--volume host:container`			——		Bind-mount host path to container path

The argument `-v /path/to/host/dir:/archivy/data` bind-mounts the directory `/path/to/host/dir` on the host to `/archivy/data` on the container.

If you wish to mount, say `/home/bob/data`, you would first need to create the `data` directory at `/home/bob`, and then change the argument to `-v /home/bob/data:/archivy/data`.



### Environment Variable Injection

You can inject environment variables while starting the container as follows:

```shell
$ docker run -d --name archivy -p 5000:5000 -v /path/to/host/dir:/archivy/data -e FLASK_DEBUG=1 -e ELASTICSEARCH_ENABLED=0 -e ELASTICSEARCH_URL="http://localhost:9200/" harshavardhanj/archivy
```

> `-e/--env KEY=value`							——		Set the environment variable(`key=value`)

Multiple such environment variables can be specified during run time. For now, Archivy supports the following environment variables

* `FLASK_DEBUG`                      -   Runs Flask in debug mode. More verbose output to console
* `ELASTICSEARCH_ENABLED`  -   Enables Elasticsearch support
* `ELASTICSEARCH_URL`          -   Sets the URL at which Elasticsearch listens

If the values are not set by the user, they are assigned default values during run time.

> **NOTE**:
>
> If you wish to use Archivy with Elasticsearch, read on. The setup is explained in the **Docker Compose** section below.



### Try Demo on ‘*Play With Docker*’

For those with DockerHub accounts, you can try a version of Archivy on Play With Docker by clicking on the badge below. This will require you to login to your DockerHub account.

[![Try in ‘Play With Docker’](https://github.com/play-with-docker/stacks/raw/cff22438cb4195ace27f9b15784bbb497047afa7/assets/images/button.png)](https://labs.play-with-docker.com?stack=https://raw.githubusercontent.com/HarshaVardhanJ/archivy/docker/docker-compose.yml)

This version of archivy is based on the following Docker Compose file:

```yaml
version: '3.8'
services:
  archivy:
    image: harshavardhanj/archivy
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

As is visible from the above compose file, this is a version of Archivy running without Elasticsearch enabled. Therefore, the search function will not work.

### Using Docker Compose

Docker Compose is an easier way to bring up containers when compared to running lengthy `docker run` commands. The `docker-compose.yaml` file contains all the necessary information that you would normally provide to the `docker run` command, declared in a YAML format. Once this file is written, it as simple as running the following command in the same directory as the `docker-compose.yml` file:

```sh
$ docker-compose up -d archivy
```

This works as long as the compose file is named `docker-compose.yml`. If it has a different name, you will need to specify the path to the file as an argument to the `-f` flag as shown below:

```sh
$ docker-compose -f ./compose.yml archivy up -d
```

This repository contains two compose files(for now). A version of the simpler one is given below:

```yaml
version: '3.8'
services:
  archivy:
    image: harshavardhanj/archivy
    ports:
      - "5000:5000"
    volumes:
      - archivyData:/archivy/data
    environment:
    	- FLASK_DEBUG=1
    	- ELASTICSEARCH_ENABLED=0
    	
volumes:
  archivyData:
```

This file 

- pulls the container image `harshavardhanj/archivy` from DockerHub.

- binds port `5000` on the host to port `5000` on the container.

- creates a named volume `archivyData` on the host and mounts it to the `/archivy/data` directory on the container(which is where all persistent data will be stored).
- Sets the following environment variables so that they can be used by Archivy during run time
  - `FLASK_DEBUG=1`
  - `ELASTICSEARCH_ENABLED=0`

This would be the same as running the following commands:

```sh
$ docker volume create archivyData
$ docker run -d -p 5000:5000 -v archivy:/archivy/data -e FLASK_DEBUG=1 -e ELASTICSEARCH_ENABLED=0 harshavardhanj/archivy
```

When multiple container get involved, it becomes a lot easier to deal with compose files.



### Which compose file to use?

There are currently two compose files in the repository:

- `docker-compose.yml`
- `docker-compose-with-elasticsearch.yml`

If you would like to test Archivy, just download the `docker-compose.yml` and run

```sh
$ docker-compose -f ./docker-compose.yml up -d
```

The contents of the file are shown below:

```yaml
version: '3.8'
services:
  archivy:
    image: harshavardhanj/archivy
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

This file

- pulls the `archivy` image.
- binds port `5000` on the host to port `5000` on the container.
- creates a named volume `archivyData` on the host and mounts it to the `/archivy/data` directory on the container(which is where all persistent data will be stored).

> **NOTE**:
>
> If you wish to bind-mount a folder to Archivy, modify the `volumes` as shown below:
>
> ```yaml
> services:
>   archivy:
>      ...
>      volumes:
>        - ./archivyData:/archivy/data
> 
> ```
>
> This will create a folder named `archivyData` in your current working directory. This is the folder in which all user-generated notes/bookmarks will be stored.

If you wish to test Archivy’s full capabilities with Elasticsearch, use the `docker-compose-with-elasticsearch.yml` . The usage of this file is explained in the next section.



### Running Archivy With Elasticsearch

The compose file given below will do the following:

- Set up an instance/container of Elasticsearch that listens on port 9200.
- Set up an instance/container of Archivy that listens on port 5000.
- Ensure that the two can communicate with each by setting the approprate environment variables(`ELASTICSEARCH_ENABLED` and `ELASTICSEARCH_URL`).
- Both containers have volumes attached to them to ensure data persistence.
- The containers will restart if the process running in the container fails and exits.

```yaml
version: '3.8'
services:

  archivy:
    image: harshavardhanj/archivy
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
    image: harshavardhanj/archivy
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

* For the `archivy` service
  * Pulls the `harshavardhanj/archivy` image. (`image:`)
  * Connects port `5000` on the host to port `5000` on the container. (`ports:`)
  * Creates the `archivyData` directory in the current working directory and bind-mounts it to the `/archivy/data` directory in the `archivy` container. (`volumes:`)
  * Sets the following environment variables. (`environment:`)
    * `FLASK_DEBUG=0`
    * `ELASTICSEARCH_ENABLED=1` (*required to enable Elasticsearch support*)
    * `ELASTICSEARCH_URL=http://elasticsearch:9200/ ` (*required by Archivy to connect to Elasticsearch*)
  * Sets a condition that the `archivy` container will start only after the `elasticsearch` container starts. (`depends_on:`)
* For the `elasticsearch` service
  * Pulls the `elasticsearch:7.9.0` image. (`image:`)
  * Connects port `9200` on the host to port `9200` on the container
  * Creates the `searchData` directory in the current working directory and bind-mounts it to the `/usr/share/elasticsearch/data` directory in the `elasticsearch` container.(`volumes:`)
  * Sets the following environment variable
    * `discovery.type=single-node`



## Using Docker Swarm

**To be added**

