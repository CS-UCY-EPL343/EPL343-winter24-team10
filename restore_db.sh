#!/bin/bash

# Variables
DB_CONTAINER_NAME=<container_name_or_id>
DB_NAME=mydatabase
DB_USER=root
DB_PASS=mypassword

# Copy the backup file into the Docker container
docker cp backup.sql $DB_CONTAINER_NAME:/backup.sql

# Restore the database
docker exec -i $DB_CONTAINER_NAME mysql -u$DB_USER -p$DB_PASS $DB_NAME < /backup.sql

# Clean up the backup file inside the container
docker exec -i $DB_CONTAINER_NAME rm /stock_backup.sql

echo "Database restored successfully!"
