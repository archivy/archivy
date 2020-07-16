export $(cat .flaskenv | xargs)
if [ "$ELASTICSEARCH_ENABLED" -eq "1" ]
then
	(ps aux | grep "python3 check_changes.py" | grep -v grep) || (python3 check_changes.py &)
	(systemctl is-active --quiet elasticsearch && echo "elasticsearch is running") || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
fi
FLASK_DEBUG=1 flask run
