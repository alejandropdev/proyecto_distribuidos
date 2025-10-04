#!/bin/bash

# Development environment startup script

echo "Starting development environment..."

# Stop any existing containers
docker-compose -f docker-compose.dev.yml down

# Start development environment
docker-compose -f docker-compose.dev.yml up -d sitio-a-dev sitio-b-dev

echo "✓ Development environment started"
echo ""
echo "Services running:"
echo "  - Site A (GC): http://localhost:5555"
echo "  - Site A (PUB): http://localhost:5556"
echo "  - Site B (Mock): http://localhost:5557"
echo ""
echo "To test PS client: ./docker-scripts/test.sh"
echo "To run load test: ./docker-scripts/load.sh"
echo "To view logs: ./docker-scripts/logs.sh"
echo "To stop: ./docker-scripts/stop.sh"
