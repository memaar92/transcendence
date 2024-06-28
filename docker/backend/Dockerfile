FROM python:3.10.12-slim

ARG APP_DIR=/app

# Set the same environment variable in the container
ENV APP_DIR=${APP_DIR}

# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1

# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

WORKDIR ${APP_DIR}

COPY tools/requirements.txt ${APP_DIR}/requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

WORKDIR ${APP_DIR}/backend

COPY scripts/backend.sh /backend.sh
RUN chmod +x /backend.sh

EXPOSE 8000

ENTRYPOINT ["/backend.sh"]

# CMD daphne -b 0.0.0.0 backend.asgi:application