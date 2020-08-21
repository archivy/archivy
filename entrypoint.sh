#!/usr/bin/env bash
#
#: Title        : entrypoint.sh
#: Date         :	19-Aug-2020
#: Author       :	"Harsha Vardhan J" <vardhanharshaj@gmail.com>
#: Version      : 0.1
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
#                   ./entrypoint.sh start    -  This will start Archivy
#                   ./entrypoint.sh command  -  This will run "command"
# 
#: Usage        :	Call the script with the appropriate argument
#
#                   ./entrypoint.sh start
#                   ./entrypoint.sh bash
#                   ./entrypoint.sh sleep 60
################


# Function used to export variables set at run time.
# The function below was taken from the 'entrypoint.sh' script that the Postgres Dockerfile refers to, and modified.
# This function is called by the 'setup' function. There is no necessity to call this function outside the 'setup' function.
#
# usage: env_export VAR [VALUE]
#     ie: env_export 'FLASK_DEBUG' '0'
#
env_export() {
  # Assign first argument to the 'var' variable
  local var="$1"

  # Assign second argument to the 'val' variable
  local val="${2:-}"

  # If the variable that 'var' points to is set
  if [[ "${!var:-}" ]]; then
    # Set 'val' to the value of the variable that 'var' points to
    val="${!var}"

    # Export the variable that 'var' points to
    export "$var"="$val"
  #else
  #  printf '%s\n' "${var} is unset." 1>&2
  fi
}


# This function exports variables only if they have not been set previously
#
# usage: env_export_check VAR [VALUE]
#     ie: env_export_check 'FLASK_DEBUG' '0'
#
env_export_check() {
  # Assigns the first argument to the 'variableName' variable
  local variableName="$1"

  # Assigns the second argument to the 'variableValue' variable
  local variableValue="${2:-}"

  # If the variable that 'variableName' points to is not set
  if [[ ! "${!variableName:-}" ]] ; then
    # Export the variable
    export "${variableName}"="${variableValue}"
  fi
}


# Function used to export variables defined in the '.flaskenv' file
#
# usage: flaskvar_export VAR [VALUE]
#     ie: flaskvar_export 'FLASK_DEBUG' '0'
#
#
flaskvar_export() {
  # If the '.flaskenv' file is present
  if [[ -f .flaskenv ]]; then
    # Run through all lines in the file and export the variables defined
    # if they haven't been set already
    while IFS="=" read -r variableName variableValue ; do
      env_export_check "${variableName}" "${variableValue:-}"
    done < .flaskenv
  else
    printf '%s\n' "Could not find .flaskenv file. Setting default values." 1>&2
    # Loop through all environment variables with their default values
    for envVar in "FLASK_DEBUG=0" "ELASTICSEARCH_ENABLED=0" "ELASTICSEARCH_URL='http://elasticsearch:9200/'" ; do
      printf '%s\n' "Setting "${envVar}"" 1>&2
      export "${envVar}"
    done
  fi
}


# Function that first sets the variables defined in the 'flaskenv' file
# then overrides it with the user-supplied values at run time
#
setup() {
  # Passing variables to the 'env_export' function
  env_export FLASK_DEBUG "${FLASK_DEBUG:-0}"
  env_export ELASTICSEARCH_ENABLED "${ELASTICSEARCH_ENABLED:-0}"

  # If ELASTICSEARCH_ENABLED variable is set to 1
  if [[ "${ELASTICSEARCH_ENABLED}" -eq 1 ]] ; then
    # Export with fallback default value for URL
    env_export ELASTICSEARCH_URL "${ELASTICSEARCH_URL:-"http://elasticsearch:9200/"}"
  else
    # Export as default value
    export ELASTICSEARCH_URL="http://elasticsearch:9200/"
  fi

  # Exporting all variables defined in the '.flaskenv' file
  flaskvar_export
}


# Function that checks if elasticsearch is up and running.
# If it is running, the function returns 1, else 0.
#
# Function input    :   Accepts none.
#
# Function output   :   Returns 0 if the elasticsearch instance is up
#                       Returns 1 if it is not
# 
check_elasticsearch() {
  # If the variable pointing to elasticsearch URL has been set AND
  # is not an empty string
  if [[ -v ELASTICSEARCH_URL && -n "${ELASTICSEARCH_URL}" ]] ; then
    # Use different query commands based on the tools available
    if [[ $(command -v nc) ]] ; then
      # Query the Elasticsearch URL
      elasticExists="$(echo -ne 'GET / HTTP/1.0\r\n\r\n' | nc localhost 9200 2>/dev/null | grep -o "version")"
    elif [[ $(command -v curl) ]] ; then
      # Query the Elasticsearch URL
      elasticExists="$(curl -XGET --silent "${ELASTICSEARCH_URL}" | grep -o "version")"
    else
      printf '%s\n' "Please install either netcat or curl. Required for health checks on Elasticsearch" 1>&2
      exit 1
    fi

    # If the query result is not an empty string
    if [[ -n "${elasticExists}" ]] ; then
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
  if [[ ${ELASTICSEARCH_ENABLED} -eq 1 ]] ; then
    # Run until the 'check_elasticsearch' function returns 0
    until [[ $(check_elasticsearch) -eq 0 ]] ; do
      printf '%s\n' "Waiting for Elasticsearch @ "${ELASTICSEARCH_URL}" to start." 1>&2
      sleep 2
    done
  fi
}


# Main function
# Runs the Archivy server if the "start" argument is provided.
# Runs any command if passed instead of the "start" argument.
#
main() {
  # Calling the setup function which takes care of setting environment variables
  setup || printf '%s\n' "'setup' function failed" 1>&2

  # Activate virtual environment
  source venv/bin/activate

  # If elasticsearch is enabled and if DEPLOY_ENV is not set
  if [[ -z "${DEPLOY_ENV}" && ${ELASTICSEARCH_ENABLED} -eq 1 ]] ; then
    (pkill -f check_changes.py)
    (python3 check_changes.py &)
  fi

  # If the first argument is "start"
  if [[ "$1" = "start" ]] ; then
    # Calling the function which will wait until elasticsearch has started
    waitforElasticsearch

    # Run the flask server in foreground
    exec flask run --host=0.0.0.0
  else
    # Executing any arguments passed to the script
    # This is useful when the container needs to be run in interactive mode
    exec "$@"
  fi
}


# Calling the main function and passing all arguments to it
main "$@"

################## End of script
