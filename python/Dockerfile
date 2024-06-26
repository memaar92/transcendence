FROM python:3.10.12-slim

ARG APP_DIR=/usr/src/transcendence

# Set the same environment variable in the container
ENV APP_DIR=${APP_DIR}

# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1

# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

WORKDIR ${APP_DIR}

COPY tools/requirements.txt ${APP_DIR}

RUN pip3 install --no-cache-dir -r requirements.txt

COPY transcendence/ ${APP_DIR}

EXPOSE 8000

# CMD python manage.py runserver
# CMD daphne backend.asgi:application -u $APP_DIR/daphne.sock

CMD daphne -b 0.0.0.0 backend.asgi:application