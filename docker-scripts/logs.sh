#!/bin/bash

# View logs script

echo "Viewing container logs..."
echo "Press Ctrl+C to exit"
echo ""

# Show logs for all services
docker-compose -f docker-compose.dev.yml logs -f
