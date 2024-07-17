#!/bin/bash

# Apply migrations
python3 manage.py makemigrations && python3 manage.py migrate || { echo "Migration failed"; exit 1; }

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput || { echo "Static files collection failed"; exit 1; }

# Read secrets
DJANGO_ADMIN_EMAIL=$(cat /run/secrets/django_admin_email)
DJANGO_ADMIN_USER=$(cat /run/secrets/django_admin_user)
DJANGO_ADMIN_PASSWORD=$(cat /run/secrets/django_admin_password)

# Check if the superuser already exists and create or update it
echo "Checking for existing superuser with email: $DJANGO_ADMIN_EMAIL"
python3 manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(email="$DJANGO_ADMIN_EMAIL", defaults={"displayname": "$DJANGO_ADMIN_USER"})
if not created:
    user.displayname = "$DJANGO_ADMIN_USER"
user.set_password("$DJANGO_ADMIN_PASSWORD")
user.is_superuser = True
user.is_staff = True
user.save()
EOF
if [ $? -ne 0 ]; then
    echo "Superuser creation or update failed"
    exit 1
fi

# Start Daphne server
exec daphne -b 0.0.0.0 backend.asgi:application
