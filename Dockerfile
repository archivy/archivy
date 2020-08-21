######## Dockerfile for Archivy Built On Debian Buster Slim  ########
#                                                                   #
#####################################################################
#     CONTAINERISED ARCHIVY BUILT ON TOP OF DEBIAN BUSTER SLIM      #
#-------------------------------------------------------------------#
#                   Built and maintained by                         #
#                       Harsha Vardhan J                            #
#               https://github.com/HarshaVardhanJ                   #
#####################################################################
#                                                                   #
# This Dockerfile does the following:                               #
#                                                                   #
#    1. Starts with a base image of Python3.8.5 built on Debian     #
#       Buster Slim.                                                #
#    2. Sets the working directory to /usr/src/app.                 #
#    3. Installs cURL, downloads the repository as a tarball,       #
#       extracts the source code, and moves all files to the        #
#       current working directory.                                  #
#    4. Creates a virtual environment, and installs all required    #
#       modules/packages as per the requirements.txt file.          #
#    5. Cleans up by deleting some unnecessary files.               #
#    6. Creates a mount point so that external volumes can be       #
#       mounted/attached to it. Useful for data persistence.        #
#    7. Exposes port 5000 on the container.                         #
#    8. Runs the startup script as the entrypoint command with      #
#       the "start" argument.                                       #
#                                                                   #
# Note : Do not forget to bind port 5000 to a port on your host if  #
#        you wish to access the server. Also, if you want your data #
#        to persist, bind-mount a directory to the container.       #
#                                                                   #
#        Example:                                                   #
#        docker run --name archivy -p 5000:5000 \                   #
#        -v "$(pwd)"/testDir:/usr/src/app/data archivy:latest       #
#                                                                   #
#        where 'testDir' is the directory on the host and           #
#        '/usr/src/app/data' is the path of the volume on the       #
#        container(fixed in Dockerfile).                            #
#                                                                   #
#####################################################################

# Starting with base image of python3.8.5 built on Debian Buster Slim
FROM python:3.8.5-slim-buster

# ARG values for injecting metadata during build time
# NOTE: When using ARGS in a multi-stage build, remember to redeclare
#       them for the stage that needs to use it. ARGs last only for the
#       lifetime of the stage that they're declared in.
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Setting working directory
WORKDIR /usr/src/app

# Updating repo, and installing curl
RUN apt update && apt install --no-install-recommends -y curl \
    # Downloading a tarball of the repository and extracting it
    && curl -sL https://github.com/Uzay-G/archivy/tarball/master | tar -xz \
    && cd Uzay-G* \
    && cp -Rp . ../. \
    && cd ../ \
    && rm -rf Uzay-G-* \
    # Creating a virtual environment
    && python3 -m venv venv/ \
    # Installing required packages
    && pip3 install --no-cache-dir -r requirements.txt \
    # Cleaning up
    && apt remove wget -y \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/* \
    && rm -rf /var/lib/apt \
    && rm -rf /var/lib/dpkg \
    && rm -f /usr/src/app/archivy.gif \
    && rm -f /usr/src/app/*.md

# Creating mount point for persistent data
VOLUME /usr/src/app/data

# Exposing port 5000
EXPOSE 5000

# System call signal that will be sent to the container to exit
STOPSIGNAL SIGTERM

# Entrypoint - Run 'entrypoint.sh' script. Any command given to 'docker container run' will be added as an argument
# to the ENTRYPOINT command below. The 'entrypoint.sh' script needs to receive 'start' as an argument in order to set up
# the Archivy server.
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# The 'start' CMD is required by the 'entrypoint.sh' script to set up the Archivy server. 
# Any command given to the 'docker container run' will override the CMD below which
# will result in the Archivy not being set up. 
CMD ["start"]

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
