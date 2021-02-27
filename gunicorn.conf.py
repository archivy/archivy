# configuration file for running Archivy thru gunicorn
# See https://docs.gunicorn.org/en/latest/settings.html#settings for configuration settings


accesslog = '-'
bind = "127.0.0.1:5000"
capture_output = True
errorlog = '-'
loglevel = 'info'
max_requests = 500
workers = 1
