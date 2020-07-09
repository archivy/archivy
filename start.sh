export $(cat .flaskenv | xargs)
systemctl is-active --quiet elasticsearch && echo "elasticsearch is running" || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
FLASK_DEBUG=1 flask run
