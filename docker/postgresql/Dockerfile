# Use an official PostgreSQL runtime as a parent image
FROM postgres:latest


# COPY ./init.sql /docker-entrypoint-initdb.d/

# Set environment variable for data directory (this should match the volume in docker-compose)
ENV PGDATA=/var/lib/postgresql/data/pgdata



# When the container starts, this script will be executed
