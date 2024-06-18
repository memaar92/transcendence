# Use an official PostgreSQL runtime as a parent image
FROM postgres:latest

RUN pg_ctl stop
#RUN rm -rf /var/lib/postgresql/pgdata
RUN usermod -u 102966 -o postgres
RUN mkdir -p /var/lib/postgresql/data/pgdata/
RUN chmod -R 777 /var/lib/postgresql/data/pgdata/

RUN pg_ctl start
# Set environment variable for data directory (this should match the volume in docker-compose)
#ENV PGDATA=/var/lib/postgresql/data/pgdata



# When the container starts, this script will be executed
COPY ./init.sql /docker-entrypoint-initdb.d/
