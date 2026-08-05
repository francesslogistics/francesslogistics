python manage.py migrate
python manage.py loaddata datadump.json
gunicorn francess_backend.wsgi
