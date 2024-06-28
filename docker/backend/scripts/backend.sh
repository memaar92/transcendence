#!/bin/bash

python3 manage.py makemigrations && python3 manage.py migrate

daphne -b 0.0.0.0 backend.asgi:application

tail -f /dev/null