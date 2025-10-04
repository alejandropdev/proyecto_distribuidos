#!/bin/bash

# Build script for Docker containers

echo "Building Docker containers for Distributed Library System..."

# Build the main image
docker build -t dist-biblio:latest .

echo "✓ Docker image built successfully"
echo "Image: dist-biblio:latest"
echo ""
echo "Available commands:"
echo "  ./docker-scripts/dev.sh     - Start development environment"
echo "  ./docker-scripts/test.sh    - Run PS client test"
echo "  ./docker-scripts/load.sh    - Run load test"
echo "  ./docker-scripts/stop.sh    - Stop all containers"
echo "  ./docker-scripts/logs.sh    - View logs"
