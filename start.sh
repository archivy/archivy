export $(cat .flaskenv | xargs)
if [ "$ELASTICSEARCH_ENABLED" -eq "1" ]
then
	(systemctl is-active --quiet elasticsearch && echo "elasticsearch is running") || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
	(pkill -f check_changes.py)
	(python3 check_changes.py &)
fi
FLASK_DEBUG=1 flask run
