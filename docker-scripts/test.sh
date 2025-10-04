#!/bin/bash

# PS Client test script

echo "Running PS client test..."

# Ensure development environment is running
docker-compose -f docker-compose.dev.yml up -d sitio-a-dev sitio-b-dev

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Run PS client test
docker-compose -f docker-compose.dev.yml run --rm ps-test

echo "✓ PS client test completed"
echo "Check metrics/results.csv for results"
