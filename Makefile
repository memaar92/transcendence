# Makefile

.DEFAULT_GOAL := all

all:
	docker-compose up --build 

up:
	docker-compose up -d

it:
	docker-compose up

down:
	docker-compose down

execbackend:
	docker exec -it backend /bin/bash

execfrontend:
	docker exec -it frontend /bin/bash

execnginx:
	docker exec -it nginx /bin/sh

re_backend:
	docker compose stop backend
	docker rmi -f $$(docker images | grep backend | awk '{print $$3}')
	docker compose up -d --build backend

re_frontend:
	docker compose stop frontend
	docker rmi -f $$(docker images | grep frontend | awk '{print $$3}')
	docker compose up -d --build frontend

re_nginx:
	docker compose stop nginx
	docker rmi -f $$(docker images | grep nginx | awk '{print $$3}')
	docker compose up -d --build nginx.

re_postgresql:
	docker compose stop postgresql
	docker rmi -f $$(docker images | grep postgresql | awk '{print $$3}')
	docker compose up -d --build nginx

restart_backend:
	docker restart $$(docker ps -a | grep backend | awk '{print $$1}')

fclean: down
	docker system prune -af

dclean:
	docker-compose -f docker-compose.yml down -v --rmi local
	docker system prune --all --force --volumes

re: fclean all

.PHONY: all up down build execbackend execfrontend execnginx re_backend restart_backend re_frontend fclean re
