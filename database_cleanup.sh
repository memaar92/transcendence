#!/bin/bash

# Exit on non-zero status code
set -euo pipefail

# Create variables for the script's directory
echo ':: Setting up variables'
FOLDER_TO_DELETE="database"
CONTAINER_NAME="database_cleanup"
IMAGE_NAME="database_cleanup"
DOCKER_FOLDER="database_cleanup"

# Change into this script's directory
PROJECT_DIR=$(dirname "${BASH_SOURCE[@]}")
cd "$PROJECT_DIR"

# Bring down the database container
echo ':: Running `docker-compose down`'
docker-compose down

# Build and run a temporary container for database deletion
echo ":: Building temporary image $IMAGE_NAME"
cd "$DOCKER_FOLDER"
    docker build -t "$IMAGE_NAME" .
cd ..
echo ':: Running temporary container'
docker run --rm -it -v "$(pwd)/$FOLDER_TO_DELETE":/var/lib/mysql "$IMAGE_NAME"

# Delete the temporary container's image
echo ':: Removing temporary image'
docker image rm "$IMAGE_NAME"

# Re-create the initial directory
echo ':: Re-creating the initial directory'
rm -rf "$FOLDER_TO_DELETE"
mkdir "$FOLDER_TO_DELETE"
