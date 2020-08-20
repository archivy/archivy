#!/usr/bin/env bash
#
#: Title        : entrypoint.sh
#: Date         :	19-Aug-2020
#: Author       :	"Harsha Vardhan J" <vardhanharshaj@gmail.com>
#: Version      : 0.1
#: Description  : This file handles the startup of the 'Archivy' server
#                 and other functions necessary for its startup such as
#                 setting default environment variables and overriding
#                 the defaults with user-provided values.
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
    export FLASK_DEBUG=0 ELASTICSEARCH_ENABLED=0 ELASTICSEARCH_URL=""
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
    env_export ELASTICSEARCH_URL "${ELASTICSEARCH_URL:-"http://localhost:9200"}"
  else
    # Export as empty string
    export ELASTICSEARCH_URL=""
  fi

  # Exporting all variables defined in the '.flaskenv' file
  flaskvar_export
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
  if [[ -z "${DEPLOY_ENV}" && "$ELASTICSEARCH_ENABLED" -eq 1 ]] ; then
    (pkill -f check_changes.py)
    (python3 check_changes.py &)
  fi

  # If the first argument is "start"
  if [[ "$1" = "start" ]] ; then
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
