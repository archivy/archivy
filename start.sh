#!/usr/bin/env bash
if test -f .flaskenv; then
  export $(cat .flaskenv | xargs)
else
  echo 'Requires .flaskenv file'
  exit;
fi
source venv/bin/activate
if [[ -z "${DEPLOY_ENV}" && "$ELASTICSEARCH_ENABLED" -eq 1 ]]
then
	(systemctl is-active --quiet elasticsearch && echo "elasticsearch is running") || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
	(pkill -f check_changes.py)
	(python3 check_changes.py &)
fi
FLASK_DEBUG=1 flask run --host=0.0.0.0
