########    Dockerfile for Archivy Built On Alpine Linux     ########
#                                                                   #
#####################################################################
#        CONTAINERISED ARCHIVY BUILT ON TOP OF ALPINE LINUX         #
#####################################################################
#                                                                   #
# This Dockerfile does the following:                               #
#                                                                   #
#    1. Starts with a base image of Python3.8 built on Debian       #
#       Buster Slim to be used as builder stage.                    #
#    2. Pins a version of archivy.                                  #
#    3. Installs Archivy using pip in the /install directory.       #
#    4. Starts with Python3.8 based on Alpine 3.12 for the final    #
#       stage.                                                      #
#    5. Installs xdg-utils(needed by archivy for opening files),    #
#       pandoc(needed by archivy for extended markdown support),    #
#       creates a non-root user account and group which will be     #
#       used to run run Archivy, creates the directory which        #
#       Archivy uses to store its data, and changes ownership of    #
#       all files in user's home directory.                         #
#    6. Copies binaries and libraries of Archivy from the builder   #
#       stage. Copies the entrypoint.sh and healthcheck.sh script   #
#       from the host. The ownership of all copied files is set to  #
#       archivy user and group.                                     #
#    7. Creates a mount point so that external volumes can be       #
#       mounted/attached to it. Useful for data persistence.        #
#    8. Exposes port 5000 on the container.                         #
#    9. Sets a command which will be to check the health of the     #
#       container.                                                  #
#   10. Runs the startup script as the entrypoint command with      #
#       the "run" argument.                                         #
#                                                                   #
# Note : Do not forget to bind port 5000 to a port on your host if  #
#        you wish to access the server. Also, if you want your data #
#        to persist, bind-mount a directory to the container.       #
#                                                                   #
#        Example:                                                   #
#        docker run --name archivy -p 5000:5000 -v \                #
#        "$(pwd)"/testDir:/archivy/data archivy:latest              #
#                                                                   #
#        where 'testDir' is the directory on the host and           #
#        '/archivy/data' is the path of the volume on the           #
#        container(fixed in Dockerfile).                            #
#                                                                   #
#####################################################################

# Starting with base image of python3.9 built on Debian Buster Slim
FROM python:3.9-slim AS builder

# Archivy version
ARG VERSION

# Installing pinned version of Archivy using pip
RUN pip3.9 install --prefix=/install archivy==$VERSION


# Starting with a base image of python:3.8-alpine for the final stage
FROM python:3.9-alpine

# ARG values for injecting metadata during build time
# NOTE: When using ARGS in a multi-stage build, remember to redeclare
#       them for the stage that needs to use it. ARGs last only for the
#       lifetime of the stage that they're declared in.
ARG BUILD_DATE
ARG VCS_REF

# Archivy version
ARG VERSION

# Installing xdg-utils and pandoc
RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
    && apk update && apk add --no-cache \
        xdg-utils \
        pandoc@testing \
        musl=1.1.24-r10 \
    # Creating non-root user and group for running Archivy
    && addgroup -S -g 1000 archivy \
    && adduser -h /archivy -g "User account for running Archivy" \
    -s /sbin/nologin -S -D -G archivy -u 1000 archivy \
    # Creating directory in which Archivy's files will be stored
    # (If this directory isn't created, Archivy exits with a "permission denied" error)
    && mkdir -p /archivy/data \
    # Changing ownership of all files in user's home directory
    && chown -R archivy:archivy /archivy

# Copying binaries and libraries from builder stage
COPY --from=builder --chown=archivy:archivy /install /usr/local/
# Copying entrypoint and healthcheck script from host
COPY --chown=archivy:archivy entrypoint.sh healthcheck.sh /usr/local/bin/

# Run as user 'archivy'
USER archivy

# Creating mount point for persistent data
VOLUME /archivy/data

# Exposing port 5000
EXPOSE 5000

# System call signal that will be sent to the container to exit
STOPSIGNAL SIGTERM

# Healthcheck command used to check if Archivy is up and running
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=5 CMD healthcheck.sh

# Entrypoint - Run 'entrypoint.sh' script. Any command given to 'docker container run' will be added as an argument
# to the ENTRYPOINT command below. The 'entrypoint.sh' script needs to receive 'run' as an argument in order to set up
# the Archivy server.
ENTRYPOINT ["entrypoint.sh"]

# The 'run' CMD is required by the 'entrypoint.sh' script to set up the Archivy server. 
# Any command given to the 'docker container run' will override the CMD below.
CMD ["run"]

# Labels
LABEL org.opencontainers.image.vendor="Uzay G" \
      org.opencontainers.image.authors="https://github.com/Uzay-G" \
      org.opencontainers.image.title="Archivy" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/Uzay-G/archivy/tree/master/" \
      org.label-schema.vcs-url="https://github.com/Uzay-G/archivy/tree/master/" \
      org.opencontainers.image.documentation="https://github.com/Uzay-G/archivy/blob/master/README.md" \
      org.opencontainers.image.source="https://github.com/Uzay-G/archivy/blob/docker/Dockerfile" \
      org.opencontainers.image.description="Archivy is a self-hosted knowledge repository that \
      allows you to safely preserve useful content that contributes to your knowledge bank." \
      org.opencontainers.image.created=$BUILD_DATE \
      org.label-schema.build-date=$BUILD_DATE \
      org.opencontainers.image.revision=$VCS_REF \
      org.label-schema.vcs-ref=$VCS_REF \
      org.opencontainers.image.version=$VERSION \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0" \
      software.author.repository="https://github.com/Uzay-G/archivy" \
      software.release.version=$VERSION
