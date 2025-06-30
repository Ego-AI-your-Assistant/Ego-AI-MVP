#!/bin/bash

# Script to fix MongoDB authentication issues
echo "Fixing MongoDB authentication issues..."

# Stop and remove the existing MongoDB container and volume
echo "Stopping and removing existing MongoDB container..."
docker-compose down mongo
docker volume rm ego_ai_mongo_data 2>/dev/null || true

# Rebuild and start the MongoDB service with the new initialization script
echo "Starting MongoDB with proper initialization..."
docker-compose up -d mongo

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to initialize..."
sleep 10

# Test the connection
echo "Testing MongoDB connection..."
docker-compose exec mongo mongosh --eval "
  use ego_ai_db;
  db.auth('ego_mongo_user', 'ego_mongo_pass');
  db.chat_history.insertOne({test: 'connection'});
  db.chat_history.deleteOne({test: 'connection'});
  print('MongoDB connection test successful!');
"

echo "MongoDB fix completed!"