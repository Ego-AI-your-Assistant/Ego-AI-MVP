#!/bin/bash

# Start all ML services in parallel
echo "Starting ML services..."

# Start chat service on port 8001
echo "Starting chat service on port 8001..."
uvicorn chat:app --host 0.0.0.0 --port 8001 &

# Start rescheduler service on port 8002
echo "Starting rescheduler service on port 8002..."
uvicorn rescheduler:app --host 0.0.0.0 --port 8002 &

# Start geo recommender service on port 8003
echo "Starting geo recommender service on port 8003..."
uvicorn geo_recommender:app --host 0.0.0.0 --port 8003 &

# Wait for all background processes
wait
