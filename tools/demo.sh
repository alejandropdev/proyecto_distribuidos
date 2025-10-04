#!/bin/bash

# Demo script for distributed library system
# Runs a complete demonstration of the system components

set -e  # Exit on any error

echo "=========================================="
echo "Distributed Library System Demo"
echo "=========================================="

# Configuration
GC_MODE=${1:-serial}  # Default to serial, can pass "threaded"
DEMO_DURATION=30      # Shorter demo duration
PS_PER_SITE=2         # Fewer PS for demo

echo "Configuration:"
echo "  GC Mode: $GC_MODE"
echo "  Demo Duration: ${DEMO_DURATION}s"
echo "  PS per Site: $PS_PER_SITE"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
mkdir -p metrics data/ejemplos

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create sample data if it doesn't exist
if [ ! -f "data/ejemplos/peticiones_sample.txt" ]; then
    echo "Creating sample request file..."
    cat > data/ejemplos/peticiones_sample.txt << EOF
PRESTAR ISBN-0001 u-1
RENOVAR ISBN-0100 u-17
DEVOLVER ISBN-0099 u-5
PRESTAR ISBN-0002 u-2
RENOVAR ISBN-0101 u-18
DEVOLVER ISBN-0102 u-6
PRESTAR ISBN-0003 u-3
RENOVAR ISBN-0103 u-19
DEVOLVER ISBN-0104 u-7
PRESTAR ISBN-0004 u-4
RENOVAR ISBN-0105 u-20
DEVOLVER ISBN-0106 u-8
PRESTAR ISBN-0005 u-5
RENOVAR ISBN-0107 u-21
DEVOLVER ISBN-0108 u-9
PRESTAR ISBN-0006 u-6
RENOVAR ISBN-0109 u-22
DEVOLVER ISBN-0110 u-10
PRESTAR ISBN-0007 u-7
RENOVAR ISBN-0111 u-23
DEVOLVER ISBN-0112 u-11
PRESTAR ISBN-0008 u-8
RENOVAR ISBN-0113 u-24
DEVOLVER ISBN-0114 u-12
PRESTAR ISBN-0009 u-9
RENOVAR ISBN-0115 u-25
DEVOLVER ISBN-0116 u-13
EOF
fi

echo ""
echo "=========================================="
echo "Step 1: Starting GC Server"
echo "=========================================="

# Start GC server in background
echo "Starting GC server in $GC_MODE mode..."
python -m gc.server --mode $GC_MODE --pretty &
GC_PID=$!

# Wait for GC to start
sleep 3

echo "GC server started (PID: $GC_PID)"
echo ""

echo "=========================================="
echo "Step 2: Testing Individual PS Client"
echo "=========================================="

# Test individual PS client
echo "Testing PS client with sample requests..."
python -m ps.client --sede A --file data/ejemplos/peticiones_sample.txt --pretty --delay 100

echo ""
echo "=========================================="
echo "Step 3: Running Load Test"
echo "=========================================="

# Run load test
echo "Running load test for ${DEMO_DURATION}s..."
python tools/spawn_ps.py \
    --ps-per-site $PS_PER_SITE \
    --sites A,B \
    --duration-sec $DEMO_DURATION \
    --file data/ejemplos/peticiones_sample.txt \
    --gc tcp://127.0.0.1:5555 \
    --mode $GC_MODE \
    --out metrics/results.csv

echo ""
echo "=========================================="
echo "Step 4: Generating Charts"
echo "=========================================="

# Generate charts
echo "Generating performance charts..."
python tools/charts.py --csv metrics/results.csv --outdir metrics/

echo ""
echo "=========================================="
echo "Step 5: Cleanup"
echo "=========================================="

# Stop GC server
echo "Stopping GC server..."
kill $GC_PID 2>/dev/null || true
wait $GC_PID 2>/dev/null || true

echo ""
echo "=========================================="
echo "Demo Complete!"
echo "=========================================="

echo ""
echo "Results:"
echo "  Metrics CSV: metrics/results.csv"
echo "  Latency Chart: metrics/latency_vs_ps.png"
echo "  Throughput Chart: metrics/throughput_vs_ps.png"

if [ -f "metrics/results.csv" ]; then
    echo ""
    echo "Sample metrics:"
    head -5 metrics/results.csv
fi

echo ""
echo "To run with threaded mode: ./tools/demo.sh threaded"
echo "To run longer test: modify DEMO_DURATION in this script"
