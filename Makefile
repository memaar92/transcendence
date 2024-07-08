up:
	docker-compose up -d

build:
	docker-compose up --build

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

execpostgres:
	docker exec -it postgres /bin/bash

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

re_postgres:
	docker compose stop postgres
	docker rmi -f $$(docker images | grep postgres | awk '{print $$3}')
	docker compose up -d --build nginx

restart_backend:
	docker restart $$(docker ps -a | grep backend | awk '{print $$1}')

fclean: down
	docker system prune -af

dclean:
	docker-compose -f docker-compose.yml down -v --rmi local
	docker system prune --all --force --volumes

re: fclean all

.PHONY: up down build execbackend execfrontend execnginx re_backend restart_backend re_frontend fclean re dclean re_postgres re_nginx execpostgres
