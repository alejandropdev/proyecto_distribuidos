#!/bin/bash

# Quick Start Script for Distributed Library System
# This script provides the easiest way to get started

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Distributed Library System - Quick Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}Choose your preferred method:${NC}"
echo ""
echo "1. Python Menu Interface (Recommended)"
echo "2. Docker Menu Interface"
echo "3. Quick Docker Start"
echo "4. Show Help"
echo ""

read -p "Select option (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}Starting Python menu interface...${NC}"
        python run_system.py
        ;;
    2)
        echo -e "${GREEN}Starting Docker menu interface...${NC}"
        ./docker-scripts/menu.sh menu
        ;;
    3)
        echo -e "${GREEN}Starting Docker system...${NC}"
        ./docker-scripts/menu.sh start
        ;;
    4)
        echo ""
        echo -e "${YELLOW}Available Options:${NC}"
        echo ""
        echo "1. Python Menu Interface:"
        echo "   - Interactive menu with all options"
        echo "   - Works with or without Docker"
        echo "   - Real-time monitoring and testing"
        echo ""
        echo "2. Docker Menu Interface:"
        echo "   - Docker-specific operations"
        echo "   - Container management"
        echo "   - Log viewing and testing"
        echo ""
        echo "3. Quick Docker Start:"
        echo "   - Automatically starts the full system"
        echo "   - Best for quick testing"
        echo ""
        echo "For more information, see:"
        echo "  - README.md - Project overview"
        echo "  - MANUAL_USAGE_GUIDE.md - Detailed usage guide"
        echo "  - DOCKER.md - Docker-specific information"
        ;;
    *)
        echo -e "${RED}Invalid option. Please run the script again.${NC}"
        exit 1
        ;;
esac
