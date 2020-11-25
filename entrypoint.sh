#!/usr/bin/env sh
#
#: Title        : entrypoint.sh
#: Date         : 19-Aug-2020
#: Version      : 0.3
#: Description  : This file handles the startup of the 'Archivy' server
#                 and other functions necessary for its startup such as
#                 setting default environment variables and overriding
#                 the defaults with user-provided values. Also, if
#                 Elasticsearch support is enabled, the script waits for
#                 it to start up before running the Archivy server.
#                 
#: Options      : Takes at least one argument, which is provided by the
#                 Dockerfile. Any commands/arguments passed to the container
#                 during startup will be run by the script and the Archivy
#                 process will not be run.
#
#                   ./entrypoint.sh run          -  This will run Archivy
#                   ./entrypoint archivy command -  This will run "archivy command"
#                   ./entrypoint.sh command      -  This will run "command"
# 
#: Usage        :	Call the script with the appropriate argument
#
#                   ./entrypoint.sh run
#                   ./entrypoint.sh archivy --version
#                   ./entrypoint.sh bash
#                   ./entrypoint.sh sleep 60
################


# Function used to export variables.
#
# usage: env_export VAR [VALUE]
#     ie: env_export 'FLASK_DEBUG' '0'
#
env_export() {
  # Assign first argument to the 'var' variable
  variableName="$1"

  # Assign second argument to the 'val' variable
  variableValue="${2:-}"

  # Export variable with provided value
  export "${variableName}"="${variableValue}"
}


# Function that sets user-defined variables along with
# sensible defaults.
#
# Function input    :   None
# Function output   :   None. Sets environment variables.
#
setup() {
  # Setting environment variables(with sensible defaults)
  env_export FLASK_DEBUG "${FLASK_DEBUG:-0}"
  env_export ELASTICSEARCH_ENABLED "${ELASTICSEARCH_ENABLED:-0}"
  env_export ARCHIVY_PORT "5000"
  env_export ARCHIVY_DATA_DIR "/archivy"

  # If ELASTICSEARCH_ENABLED variable is set to 1
  if [ ${ELASTICSEARCH_ENABLED} -eq 1 ] ; then
    # Export with fallback default value for URL
    env_export ELASTICSEARCH_URL "${ELASTICSEARCH_URL:-"http://localhost:9200/"}"
  else
    # Export as default value
    env_export ELASTICSEARCH_URL "http://localhost:9200/"
  fi
}


# Function that checks if elasticsearch is up and running.
# If it is running, the function returns 0, else 1.
#
# Function input    :   Accepts none.
#
# Function output   :   Returns 0 if the elasticsearch instance is up
#                       Returns 1 if it is not
# 
check_elasticsearch() {
  # Get hostname and port from ELASTICSEARCH_URL variable's value.
  # Required for use with netcat as the host and port will have to be passed
  # as separate arguments to it.
  elasticHostname="$(echo "${ELASTICSEARCH_URL}" | awk -F[:/] '{print $4}')"
  elasticPort="$(echo "${ELASTICSEARCH_URL}" | awk -F[:/] '{print $5}')"

  # If the variable pointing to elasticsearch URL is not an empty string
  if [ "$( echo "${ELASTICSEARCH_URL}" )" != "" ] ;  then
    # Use different query commands based on the tools available
    if [ $(command -v wget) ] ; then
      # Query the Elasticsearch URL
      elasticExists="$(wget -qO- "${ELASTICSEARCH_URL}" 2>/dev/null | grep -o "version" )"
    elif [ $(command -v curl) ] ; then
      # Query the Elasticsearch URL
      elasticExists="$(curl -X GET --silent "${ELASTICSEARCH_URL}" | grep -o "version")"
    else
      printf '%s\n' "Please install either wget or curl. Required for health checks on Elasticsearch." 1>&2
      exit 1
    fi

    # If the query result is not an empty string
    if [ "$( echo "${elasticExists}" )" != "" ] ; then
      return 0
    else
      return 1
    fi
  # If the variable pointing to elasticseach's URL has not been set
  else
    # Run the 'setup' function which will set sensible defaults
    setup
    return 1
  fi
}


# Function that waits until Elasticsearch has started up.
#
# Function input    :   None
#
# Function output   :   None
#
waitforElasticsearch() {
  # Loop that waits for Elasticsearch to start up before running Archivy
  # If Elasticsearch support has been enabled
  if [ ${ELASTICSEARCH_ENABLED} -eq 1 ] ; then
    # Run the 'check_elasticsearch' function
    check_elasticsearch
    # Run until function's exit code is 0
    until [ $? -eq 0 ] ; do
      printf '%s\n' "Waiting for Elasticsearch @ "${ELASTICSEARCH_URL}" to start." 1>&2
      sleep 2
      # Run function
      check_elasticsearch
    done
    printf '%s\n' "Elasticsearch is running @ "${ELASTICSEARCH_URL}"."
  else
    printf '%s\n' "ELASTICSEARCH_ENABLED variable is set to ${ELASTICSEARCH_ENABLED}. Expected 1." 1>&2
    exit 1
  fi
}


# Main function
# Runs the Archivy server if the "run" argument is provided.
# Runs "archivy [argument]" if "archivy [argument]" are provided as arguments.
# Runs any command if passed instead of the "archivy" argument.
#
main() {
  printf '%s\n' "Setting environment variables."
  # Calling the setup function which takes care of setting environment variables
  setup || printf '%s\n' "'setup' function failed" 1>&2

  # Printing environment variables set
  printf '%s\n' "The following environment variables were set:"
  for varName in "FLASK_DEBUG" "ELASTICSEARCH_ENABLED" "ELASTICSEARCH_URL" "ARCHIVY_PORT"; do
    varVal="$( eval echo "\$${varName}" )"
    printf '\t\t%s\n' "${varName}=${varVal}"
  done

  case "$1" in
    # If the first argument is "run"
    "run")
      # If support for Elasticsearch is enabled
      if [ ${ELASTICSEARCH_ENABLED} -eq 1 ] ; then
        printf '%s\n' "Checking if Elasticsearch is up and running"
        # Calling the function which will wait until elasticsearch has started
        waitforElasticsearch
      else
        printf '%s\n' "Elasticsearch not used. Search function will not work."
      fi
      # Starting archivy
      printf '%s\n' "Starting Archivy"
      exec archivy run
      ;;
    # If the first argument is "archivy"
    "archivy")
      # Passing any arguments passed to the script to Archivy
      printf '%s\n' "Running ""$@"""
      exec archivy "$2"
      ;;
    # If the first argument is neither "run" nor "archivy"
    *)
      # Running the commands given as arguments
      exec "$@"
      ;;
  esac
}


# Calling the main function and passing all arguments to it
main "$@"

################## End of script
