export $(cat .flaskenv | xargs)
python3 check_changes.py &
systemctl is-active --quiet elasticsearch && echo "elasticsearch is running" || (echo "Enter password to enable elasticsearch" && sudo service elasticsearch restart)
FLASK_DEBUG=1 flask run
