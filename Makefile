.phony: all build stop clean fclean prune fprune

all:
	- mkdir /home/$(USER)/transdata/
	- mkdir /home/$(USER)/transdata/database_volume
	docker-compose -f srcs/docker-compose.yml up -d

activate:
	source ./djangoenv/bin/activate

build:
	docker-compose -f srcs/docker-compose.yml build

stop:
	docker-compose -f srcs/docker-compose.yml stop

clean:
	docker-compose -f srcs/docker-compose.yml down -v

fclean:
	docker-compose -f srcs/docker-compose.yml down -v --rmi local
	rm -rf /home/$(USER)/transdata

prune:
	docker system prune --all --force --volumes

fprune: fclean prune