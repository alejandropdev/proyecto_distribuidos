#!/bin/bash

# Stop all containers script

echo "Stopping all containers..."

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# Stop production environment (if running)
docker-compose down

echo "✓ All containers stopped"
