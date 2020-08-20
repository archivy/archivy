#!/usr/bin/env bash


# Do not continue to run the script if
# any command exit with a non zero exit code
set -e

if test -f .flaskenv; then
  export $(cat .flaskenv | xargs)
else
  echo 'Requires .flaskenv file'
  exit 1;  # exit with non-zero exit code
fi

if which python3; then
	PYTHON=`which python3`
else
	echo "Python not found. Make sure you have python3 on PATH"
	exit 1
fi

# https://stackoverflow.com/q/15454174
if [[ "$VIRTUAL_ENV" != "" ]]; then
	echo "Already running in virtual environment."
	# this is specifically useful if you are using
	# another virtual enironment manager like 
	# pipenv, rather than python's virtualenv
else
	echo "Activating virtual env"
	if test -f venv/bin/activate; then
		source venv/bin/activate
	else
		# the user might not have created a virtual
		# environment
		echo "Virtual environment not yet created"
		echo "Automatically attempting to create virtualenv and install packages"
		$PYTHON -m venv venv/
		source venv/bin/activate
		pip3 install -r requirements.txt
		echo "Done!"
	fi
fi

if [[ -z "${DEPLOY_ENV}" && "$ELASTICSEARCH_ENABLED" -eq 1 ]]
then
	(systemctl is-active --quiet elasticsearch && echo "elasticsearch is running") || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
	(pkill -f check_changes.py)
	($PYTHON check_changes.py &)
fi
FLASK_DEBUG=1 flask run --host=0.0.0.0
