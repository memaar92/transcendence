#!/bin/bash

python3 manage.py makemigrations && python3 manage.py migrate

# Creates Admin page static files # TODO: Remove in production
# -------------------------------------
# Admin panel USERNAME: admin PASSWORD: admin
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser --noinput --username $(cat /run/secrets/django_admin_user) --email wayne@waynescoffee.ch
echo "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='$(cat /run/secrets/django_admin_user)'); user.set_password('$(cat /run/secrets/django_admin_password)'); user.save()" | python3 manage.py shell
# -------------------------------------

exec daphne -b 0.0.0.0 backend.asgi:application
