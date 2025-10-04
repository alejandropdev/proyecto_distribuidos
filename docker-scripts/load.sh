#!/bin/bash

# Load test script

echo "Running load test..."

# Ensure development environment is running
docker-compose -f docker-compose.dev.yml up -d sitio-a-dev sitio-b-dev

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Run load test
docker-compose -f docker-compose.dev.yml run --rm load-test

echo "✓ Load test completed"
echo "Check metrics/results.csv for results"
echo "To generate charts: python tools/charts.py --csv metrics/results.csv --outdir metrics/"
