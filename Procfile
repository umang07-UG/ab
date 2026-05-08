release: python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python manage.py create_admin
web: gunicorn myproject.wsgi --log-file - --bind 0.0.0.0:$PORT
