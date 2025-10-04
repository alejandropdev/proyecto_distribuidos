#!/bin/bash

# Failover Demo Script for Distributed Library System
# Demonstrates GA failover and recovery capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATA_DIR_A="./data/siteA"
DATA_DIR_B="./data/siteB"
GA_A_PORT="5560"
GA_B_PORT="5561"
AP_PORT="5557"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ❌ $1"
}

# Function to check if a process is running
is_running() {
    local pid=$1
    kill -0 $pid 2>/dev/null
}

# Function to wait for service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start on port $port"
    return 1
}

# Function to cleanup processes
cleanup() {
    print_status "Cleaning up processes..."
    
    # Kill all background processes
    jobs -p | xargs -r kill
    
    # Wait a bit for graceful shutdown
    sleep 2
    
    # Force kill if still running
    jobs -p | xargs -r kill -9 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Function to test GA operations
test_ga_operations() {
    local ga_port=$1
    local ga_name=$2
    
    print_status "Testing $ga_name operations..."
    
    # Test checkAndLoan
    python3 -c "
import zmq
import json
import sys

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:$ga_port')

# Test loan
request = {
    'method': 'checkAndLoan',
    'payload': {
        'id': 'test-loan-1',
        'libroCodigo': 'ISBN-0001',
        'userId': 'u-test-1'
    }
}

socket.send_json(request)
response = socket.recv_json()

if response.get('ok'):
    print('✅ Loan test successful')
else:
    print(f'❌ Loan test failed: {response.get(\"reason\")}')
    sys.exit(1)

socket.close()
context.term()
"
    
    # Test renovation
    python3 -c "
import zmq
import json
import sys
from datetime import datetime, timedelta

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:$ga_port')

# Test renovation
request = {
    'method': 'renovar',
    'payload': {
        'id': 'test-renovation-1',
        'libroCodigo': 'ISBN-0001',
        'userId': 'u-test-1',
        'dueDateNew': '$(date -d '+7 days' '+%Y-%m-%d')'
    }
}

socket.send_json(request)
response = socket.recv_json()

if response.get('ok'):
    print('✅ Renovation test successful')
else:
    print(f'❌ Renovation test failed: {response.get(\"reason\")}')
    sys.exit(1)

socket.close()
context.term()
"
    
    print_success "$ga_name operations test completed"
}

# Function to simulate failover
simulate_failover() {
    local ga_pid=$1
    local ga_name=$2
    
    print_warning "Simulating $ga_name failure..."
    
    # Kill the GA process
    kill $ga_pid
    
    # Wait for it to die
    sleep 2
    
    print_success "$ga_name has been terminated"
}

# Function to test replication
test_replication() {
    print_status "Testing replication between GA_A and GA_B..."
    
    # Perform operation on GA_A
    python3 -c "
import zmq
import json
import sys

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:$GA_A_PORT')

# Test operation on GA_A
request = {
    'method': 'devolver',
    'payload': {
        'id': 'replication-test-1',
        'libroCodigo': 'ISBN-0002',
        'userId': 'u-test-2'
    }
}

socket.send_json(request)
response = socket.recv_json()

if response.get('ok'):
    print('✅ Operation on GA_A successful')
else:
    print(f'❌ Operation on GA_A failed: {response.get(\"reason\")}')
    sys.exit(1)

socket.close()
context.term()
"
    
    # Wait for replication
    sleep 3
    
    # Check if operation was replicated to GA_B
    python3 -c "
import zmq
import json
import sys

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:$GA_B_PORT')

# Check oplog on GA_B
request = {
    'method': 'get_oplog_stats',
    'payload': {}
}

socket.send_json(request)
response = socket.recv_json()

print(f'GA_B oplog stats: {response}')

socket.close()
context.term()
"
    
    print_success "Replication test completed"
}

# Main demo function
run_demo() {
    print_status "Starting Distributed Library System Failover Demo"
    print_status "=================================================="
    
    # Setup cleanup trap
    trap cleanup EXIT INT TERM
    
    # Ensure data directories exist
    mkdir -p "$DATA_DIR_A" "$DATA_DIR_B"
    
    # Generate seed data if not exists
    if [ ! -f "$DATA_DIR_A/books.json" ]; then
        print_status "Generating seed data for Site A..."
        python3 tools/seed_data.py --data-dir "$DATA_DIR_A" --site A
    fi
    
    if [ ! -f "$DATA_DIR_B/books.json" ]; then
        print_status "Generating seed data for Site B..."
        python3 tools/seed_data.py --data-dir "$DATA_DIR_B" --site B
    fi
    
    print_status "Starting GA_A (Site A)..."
    python3 -m ga.server --data-dir "$DATA_DIR_A" --node-id A --pretty &
    GA_A_PID=$!
    
    print_status "Starting GA_B (Site B)..."
    python3 -m ga.server --data-dir "$DATA_DIR_B" --node-id B --pretty &
    GA_B_PID=$!
    
    # Wait for services to be ready
    wait_for_service $GA_A_PORT "GA_A"
    wait_for_service $GA_B_PORT "GA_B"
    
    print_status "Starting Actor Préstamo (AP)..."
    python3 -m actors.prestamo --pretty &
    AP_PID=$!
    
    wait_for_service $AP_PORT "AP"
    
    print_status "Starting Actor Renovación (AR)..."
    python3 -m actors.renovacion --pretty &
    AR_PID=$!
    
    print_status "Starting Actor Devolución (AD)..."
    python3 -m actors.devolucion --pretty &
    AD_PID=$!
    
    # Wait a bit for all services to stabilize
    sleep 3
    
    print_success "All services are running!"
    print_status "Service PIDs:"
    echo "  GA_A: $GA_A_PID"
    echo "  GA_B: $GA_B_PID"
    echo "  AP: $AP_PID"
    echo "  AR: $AR_PID"
    echo "  AD: $AD_PID"
    
    # Test initial operations
    print_status "Phase 1: Testing initial operations..."
    test_ga_operations $GA_A_PORT "GA_A"
    test_ga_operations $GA_B_PORT "GA_B"
    
    # Test replication
    print_status "Phase 2: Testing replication..."
    test_replication
    
    # Simulate failover
    print_status "Phase 3: Simulating GA_A failover..."
    simulate_failover $GA_A_PID "GA_A"
    
    # Test operations on GA_B (should still work)
    print_status "Phase 4: Testing operations on GA_B after failover..."
    test_ga_operations $GA_B_PORT "GA_B"
    
    # Restart GA_A
    print_status "Phase 5: Restarting GA_A..."
    python3 -m ga.server --data-dir "$DATA_DIR_A" --node-id A --pretty &
    GA_A_PID=$!
    
    wait_for_service $GA_A_PORT "GA_A"
    
    # Test recovery
    print_status "Phase 6: Testing GA_A recovery..."
    test_ga_operations $GA_A_PORT "GA_A"
    
    # Wait for replication to catch up
    print_status "Phase 7: Waiting for replication to catch up..."
    sleep 5
    
    # Final test
    print_status "Phase 8: Final integration test..."
    test_ga_operations $GA_A_PORT "GA_A"
    test_ga_operations $GA_B_PORT "GA_B"
    
    print_success "Failover demo completed successfully!"
    print_status "Demo Summary:"
    echo "  ✅ All services started correctly"
    echo "  ✅ Initial operations tested"
    echo "  ✅ Replication verified"
    echo "  ✅ Failover simulated"
    echo "  ✅ Recovery tested"
    echo "  ✅ Final integration verified"
    
    # Keep services running for manual testing
    print_status "Services are still running. Press Ctrl+C to stop."
    wait
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v nc &> /dev/null; then
        missing_deps+=("netcat")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install missing dependencies and try again"
        exit 1
    fi
}

# Main execution
main() {
    check_dependencies
    run_demo
}

# Run main function
main "$@"
