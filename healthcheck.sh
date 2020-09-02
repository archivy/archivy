#!/usr/bin/env sh
#
#: Title        : healthcheck.sh
#: Date         : 02-Sep-2020
#: Version      : 0.1
#: Description  : The script check the running status of Archivy.
#                 The exit status of this script decides whether
#                 or not the container is reported as 'healthy'
#                 by the Docker daemon.
#                 
#: Options      : None required. This will be run by Docker.
#: Usage        :	Run the script `./healthcheck.sh`. In this case,
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
  local archivyHostname="localhost"
  local archivyPort="5000"

  # If 'netcat' command is available
  if [ $(command -v nc) ] ; then
    # Get the home page of Archivy
    archivyRunning="$(echo -ne 'GET / HTTP/1.0\r\n\r\n' | nc ${archivyHostname:-"localhost"} ${archivyPort:-"5000"} 2>/dev/null | grep -oE "Archivy|New Bookmark|New Note")"
  else
    printf '%s\n' "Please install netcat. Required for health checks on Elasticsearch and Archivy." 1>&2
    exit 1
  fi

  # If the query result is not an empty string
  if [ "$( echo "${archivyRunning}" )" != "" ] ; then
    return 0
  else
    return 1
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
