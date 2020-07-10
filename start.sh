export $(cat .flaskenv | xargs)
python3 check_changes.py &
if [ "$ELASTICSEARCH_ENABLED" -eq "1" ]
then
	(systemctl is-active --quiet elasticsearch && echo "elasticsearch is running") || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
fi
FLASK_DEBUG=1 flask run
