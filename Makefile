# Makefile

.DEFAULT_GOAL := all

all:
	docker-compose up -d --build 

up:
	docker-compose up -d

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

restart_backend:
	docker restart $$(docker ps -a | grep backend | awk '{print $$1}')

re_frontend:
	docker compose stop frontend
	docker rmi -f $$(docker images | grep frontend | awk '{print $$3}')
	docker compose up -d --build frontend


# carefull :D
fclean: down
	docker system prune -af

re: fclean all

.PHONY: all up down build execbackend execfrontend execnginx re_backend restart_backend re_frontend fclean re