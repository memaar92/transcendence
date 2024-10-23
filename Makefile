SHELL := /bin/bash
UNAME := $(shell uname -s)

ifeq ($(UNAME), Darwin)
	BASE_IP = $(shell ipconfig getifaddr en0)
	SED = sed -i '' 's
else
	BASE_IP = $(shell ip -o route get to 8.8.8.8 | sed -n 's/.*src \([0-9.]\+\).*/\1/p')
	SED = sed -i 's
endif

all: get_ips build

up:
	docker-compose up -d

build: set_ip
	docker-compose up --build

it:
	docker-compose up

down:
	docker-compose down

execredis:
	docker exec -it redis /bin/bash

execbackend:
	docker exec -it backend /bin/bash

execnginx:
	docker exec -it nginx /bin/sh

execpostgres:
	docker exec -it postgres /bin/bash

re_backend:
	docker compose stop backend
	docker rmi -f $$(docker images | grep backend | awk '{print $$3}')
	docker compose up -d --build backend

re_nginx:
	docker compose stop nginx
	docker rmi -f $$(docker images | grep nginx | awk '{print $$3}')
	docker compose up -d --build nginx.

re_postgres:
	docker compose stop postgres
	docker rmi -f $$(docker images | grep postgres | awk '{print $$3}')
	docker compose up -d --build postgres

re_redis:
	docker compose stop redis
	docker rmi -f $$(docker images | grep redis | awk '{print $$3}')
	docker compose up -d --build redis

restart:
	docker-compose restart

restart_backend:
	docker restart $$(docker ps -a | grep backend | awk '{print $$1}')
	docker restart $$(docker ps -a | grep redis | awk '{print $$1}')

fclean: down
	docker system prune -af
	docker volume rm $$(docker volume ls -q | grep trans_database)

dclean:
	docker-compose -f docker-compose.yml down -v --rmi local
	docker system prune --all --force --volumes

# Usage: make createapp APP_NAME=appname
createapp:
	ifndef APP_NAME
		$(error APP_NAME is not set)
	endif
		docker-compose exec backend python manage.py startapp $(APP_NAME)

# Get Ip addresses and export them to the .dev_ips file
get_ips:
	@echo "WiFi IP: $$(ip addr show | grep inet | grep -E 'wlo|wlan|wla' | awk '{print $$2}' | cut -d/ -f1 | xargs)" && \
	echo "Ethernet IP: " $$(ip addr show | grep inet | grep -E 'enp|eth' | awk '{print $$2}' | cut -d/ -f1 | xargs) && \
	echo "Public IPv4: " $$(curl -s ifconfig.me -4) && \
	echo "Public IPv6: " $$(curl -s ifconfig.me -6);

set_ip:
	echo $(BASE_IP)
	$(SED)|BASE_IP = .*|BASE_IP = "$(BASE_IP)"|' backend/backend/settings.py
	$(SED)|ALLOWED_HOSTS = .*|ALLOWED_HOSTS = ["$(BASE_IP)", "localhost", "127.0.0.1"]|' backend/backend/settings.py

re: fclean all

.PHONY: up down build execbackend execnginx re_backend restart_backend fclean re dclean re_postgres re_nginx get_ips restart execpostgres createapp execredis re_redis
