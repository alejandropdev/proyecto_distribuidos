#!/bin/bash

# Docker Menu Script for Distributed Library System
# Provides an easy-to-use interface for Docker operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print header
print_header() {
    echo "=========================================="
    print_color $BLUE "$1"
    echo "=========================================="
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check if containers are running
check_containers() {
    local running=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
    echo $running
}

# Function to show system status
show_status() {
    print_header "System Status"
    
    if [ $(check_containers) -gt 0 ]; then
        print_color $GREEN "✓ System is running"
        echo ""
        docker-compose ps
    else
        print_color $YELLOW "⚠ System is not running"
    fi
}

# Function to start the system
start_system() {
    print_header "Starting Distributed Library System"
    
    print_color $YELLOW "Building and starting containers..."
    docker-compose up -d --build
    
    print_color $YELLOW "Waiting for services to be ready..."
    sleep 10
    
    print_color $GREEN "✓ System started successfully!"
    echo ""
    show_status
}

# Function to stop the system
stop_system() {
    print_header "Stopping Distributed Library System"
    
    print_color $YELLOW "Stopping containers..."
    docker-compose down
    
    print_color $GREEN "✓ System stopped successfully!"
}

# Function to restart the system
restart_system() {
    print_header "Restarting Distributed Library System"
    
    stop_system
    sleep 2
    start_system
}

# Function to view logs
view_logs() {
    print_header "Viewing System Logs"
    
    if [ $(check_containers) -eq 0 ]; then
        print_color $RED "System is not running. Please start it first."
        return 1
    fi
    
    print_color $YELLOW "Press Ctrl+C to stop viewing logs"
    echo ""
    docker-compose logs -f
}

# Function to view specific service logs
view_service_logs() {
    print_header "Viewing Service Logs"
    
    if [ $(check_containers) -eq 0 ]; then
        print_color $RED "System is not running. Please start it first."
        return 1
    fi
    
    echo "Available services:"
    docker-compose ps --services
    echo ""
    read -p "Enter service name: " service
    
    if [ -n "$service" ]; then
        print_color $YELLOW "Viewing logs for $service (Press Ctrl+C to stop)"
        echo ""
        docker-compose logs -f "$service"
    fi
}

# Function to run tests
run_tests() {
    print_header "Running System Tests"
    
    if [ $(check_containers) -eq 0 ]; then
        print_color $RED "System is not running. Please start it first."
        return 1
    fi
    
    print_color $YELLOW "Running load test..."
    docker-compose run --rm load-generator
    
    print_color $GREEN "✓ Tests completed!"
    echo ""
    print_color $CYAN "Results saved to metrics/results.csv"
}

# Function to generate charts
generate_charts() {
    print_header "Generating Performance Charts"
    
    if [ ! -f "metrics/results.csv" ]; then
        print_color $RED "No test results found. Please run tests first."
        return 1
    fi
    
    print_color $YELLOW "Generating charts..."
    docker-compose run --rm load-generator python tools/charts.py --csv metrics/results.csv --outdir metrics/
    
    print_color $GREEN "✓ Charts generated!"
    echo ""
    print_color $CYAN "Charts saved to metrics/ directory"
}

# Function to clean up
cleanup() {
    print_header "Cleaning Up"
    
    print_color $YELLOW "Stopping and removing containers..."
    docker-compose down -v
    
    print_color $YELLOW "Removing unused images..."
    docker image prune -f
    
    print_color $GREEN "✓ Cleanup completed!"
}

# Function to show help
show_help() {
    print_header "Docker Menu Help"
    
    echo "This script provides an easy interface for managing the distributed library system."
    echo ""
    echo "Available commands:"
    echo "  start     - Start the system"
    echo "  stop      - Stop the system"
    echo "  restart   - Restart the system"
    echo "  status    - Show system status"
    echo "  logs      - View all logs"
    echo "  service   - View specific service logs"
    echo "  test      - Run system tests"
    echo "  charts    - Generate performance charts"
    echo "  cleanup   - Clean up containers and images"
    echo "  menu      - Show interactive menu"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 test"
}

# Function to show interactive menu
show_menu() {
    while true; do
        echo ""
        print_header "Docker Management Menu"
        
        show_status
        echo ""
        print_color $YELLOW "Available Options:"
        echo "1. Start System"
        echo "2. Stop System"
        echo "3. Restart System"
        echo "4. View All Logs"
        echo "5. View Service Logs"
        echo "6. Run Tests"
        echo "7. Generate Charts"
        echo "8. Cleanup"
        echo "9. Exit"
        echo ""
        
        read -p "Select an option (1-9): " choice
        
        case $choice in
            1)
                start_system
                ;;
            2)
                stop_system
                ;;
            3)
                restart_system
                ;;
            4)
                view_logs
                ;;
            5)
                view_service_logs
                ;;
            6)
                run_tests
                ;;
            7)
                generate_charts
                ;;
            8)
                if [ $(check_containers) -gt 0 ]; then
                    read -p "This will stop all containers. Continue? (y/N): " confirm
                    if [[ $confirm =~ ^[Yy]$ ]]; then
                        cleanup
                    fi
                else
                    cleanup
                fi
                ;;
            9)
                print_color $GREEN "Goodbye!"
                exit 0
                ;;
            *)
                print_color $RED "Invalid option. Please try again."
                ;;
        esac
    done
}

# Main script logic
main() {
    cd "$PROJECT_ROOT"
    
    # Check if Docker is available
    check_docker
    
    # Handle command line arguments
    case "${1:-menu}" in
        start)
            start_system
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs
            ;;
        service)
            view_service_logs
            ;;
        test)
            run_tests
            ;;
        charts)
            generate_charts
            ;;
        cleanup)
            cleanup
            ;;
        menu)
            show_menu
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_color $RED "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
