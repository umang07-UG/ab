release: python manage.py migrate --noinput && python manage.py create_admin
web: gunicorn myproject.wsgi --log-file -
