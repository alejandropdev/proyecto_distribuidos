# Distributed Library System - User Guide

## 🚀 Quick Start

The easiest way to use the distributed library system is through our menu-driven interfaces. **No manual command execution required!**

### Option 1: Python Menu Interface (Recommended)
```bash
python run_system.py
```

### Option 2: Docker Menu Interface
```bash
./docker-scripts/menu.sh menu
```

### Option 3: Quick Start Script
```bash
./start.sh
```

---

## 📋 System Overview

This distributed library system implements a book lending system for Universidad Ada Lovelace with the following components:

- **PS (Proceso Solicitante)**: Client processes that send requests (loan, renew, return)
- **GC (Gestor Central)**: Central manager that routes requests to appropriate actors
- **AR (Actor Renovación)**: Processes renewal requests via PUB/SUB
- **AD (Actor Devolución)**: Processes return requests via PUB/SUB  
- **AP (Actor Préstamo)**: Processes loan requests via REQ/REP
- **GA (Gestor de Almacenamiento)**: Storage server with replication

### Architecture
```
PS → GC → AR/AD (PUB/SUB) → GA
PS → GC → AP (REQ/REP) → GA
GA_A ↔ GA_B (Replication)
```

---

## 🎯 Using the Python Menu Interface

The Python menu interface (`run_system.py`) provides the most comprehensive control over the system.

### Main Menu Options

1. **Setup & Data** - Generate sample data for both sites
2. **Docker Mode** - Run the complete system using Docker (Recommended)
3. **Local Mode** - Run components locally without Docker
4. **Test System** - Test the system with sample requests
5. **Load Test** - Run performance tests with configurable parameters
6. **Generate Charts** - Create performance charts from test results
7. **View Logs** - Monitor system logs in real-time
8. **Stop System** - Stop all running services
9. **Exit** - Exit the program

### Step-by-Step Usage

#### 1. First Time Setup
```bash
python run_system.py
# Select option 1: Setup & Data
```

#### 2. Start the System
```bash
python run_system.py
# Select option 2: Docker Mode (recommended)
# OR option 3: Local Mode
```

#### 3. Test the System
```bash
python run_system.py
# Select option 4: Test System
```

#### 4. Run Performance Tests
```bash
python run_system.py
# Select option 5: Load Test
# Enter duration (e.g., 60 seconds)
# Enter PS per site (e.g., 2)
```

#### 5. Generate Performance Charts
```bash
python run_system.py
# Select option 6: Generate Charts
```

#### 6. Monitor Logs
```bash
python run_system.py
# Select option 7: View Logs
# Choose service to monitor or 'all'
```

---

## 🐳 Using the Docker Menu Interface

The Docker menu interface (`./docker-scripts/menu.sh`) provides Docker-specific operations.

### Available Commands

- `./docker-scripts/menu.sh start` - Start the system
- `./docker-scripts/menu.sh stop` - Stop the system
- `./docker-scripts/menu.sh restart` - Restart the system
- `./docker-scripts/menu.sh status` - Show system status
- `./docker-scripts/menu.sh logs` - View all logs
- `./docker-scripts/menu.sh service` - View specific service logs
- `./docker-scripts/menu.sh test` - Run system tests
- `./docker-scripts/menu.sh charts` - Generate performance charts
- `./docker-scripts/menu.sh cleanup` - Clean up containers and images
- `./docker-scripts/menu.sh menu` - Show interactive menu

### Interactive Menu Usage

```bash
./docker-scripts/menu.sh menu
```

This will show an interactive menu with the same options as the command-line interface.

---

## 📊 Monitoring and Logs

### Real-Time Log Monitoring

Use the log monitor tool for advanced monitoring:

```bash
python tools/log_monitor.py --interactive
```

This provides:
- Real-time log monitoring
- ZeroMQ message monitoring
- Service status checking
- Statistics and metrics

### Available Monitoring Options

1. **Monitor Docker Logs** - Real-time Docker container logs
2. **Monitor ZeroMQ Messages** - Real-time message monitoring
3. **Show Service Status** - Check all services
4. **View Recent Logs** - Show recent log entries

### Service Status

The system shows the status of all services:
- **GC**: Central Manager (Port 5555)
- **AP**: Actor Préstamo (Port 5557)
- **AR**: Actor Renovación (PUB/SUB)
- **AD**: Actor Devolución (PUB/SUB)
- **GA-A**: Storage Server A (Port 5560)
- **GA-B**: Storage Server B (Port 5561)

---

## 🧪 Testing the System

### Automated Testing

The system includes comprehensive testing capabilities:

#### 1. System Test
Tests basic functionality with sample requests:
- Loan requests (PRESTAR)
- Renewal requests (RENOVAR)
- Return requests (DEVOLVER)

#### 2. Load Testing
Configurable performance testing:
- Duration: How long to run tests
- PS per site: Number of client processes per site
- Sites: Which sites to test (A, B, or both)

#### 3. Performance Metrics
The system measures:
- Response time (average and standard deviation)
- Throughput (requests per 2 minutes)
- Success/failure rates
- Operation distribution

### Test Results

Results are saved to `metrics/results.csv` and can be visualized with charts in the `metrics/` directory:
- `latency_vs_ps.png` - Response time vs number of PS
- `throughput_vs_ps.png` - Throughput vs number of PS

---

## 🔧 Configuration

### Environment Variables

The system uses environment variables for configuration. Key variables include:

```bash
# GC Configuration
GC_BIND=tcp://0.0.0.0:5555
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION

# Connections
GC_PUB_CONNECT=tcp://127.0.0.1:5556
AP_REQ_CONNECT=tcp://127.0.0.1:5557

# GC Mode
GC_MODE=serial  # or threaded

# Metrics
METRICS_CSV=metrics/results.csv
MEASUREMENT_WINDOW_SEC=120
```

### Data Files

The system uses JSON files for data storage:
- `data/siteA/books.json` - Books for Site A
- `data/siteA/loans.json` - Loans for Site A
- `data/siteA/oplog.json` - Operation log for Site A
- `data/siteB/books.json` - Books for Site B
- `data/siteB/loans.json` - Loans for Site B
- `data/siteB/oplog.json` - Operation log for Site B

---

## 📚 Available Operations

### 1. PRESTAR (Loan a Book)
```json
{
  "id": "unique-id",
  "sedeId": "A",
  "userId": "u-123",
  "op": "PRESTAR",
  "libroCodigo": "ISBN-0001",
  "timestamp": 1710000000000
}
```

**Expected Response:**
```json
{
  "id": "unique-id",
  "status": "OK",
  "reason": null,
  "dueDate": "2025-10-18"
}
```

### 2. RENOVAR (Renew a Loan)
```json
{
  "id": "unique-id",
  "sedeId": "A",
  "userId": "u-123",
  "op": "RENOVAR",
  "libroCodigo": "ISBN-0001",
  "timestamp": 1710000000000
}
```

**Expected Response:**
```json
{
  "id": "unique-id",
  "status": "RECIBIDO"
}
```

### 3. DEVOLVER (Return a Book)
```json
{
  "id": "unique-id",
  "sedeId": "A",
  "userId": "u-123",
  "op": "DEVOLVER",
  "libroCodigo": "ISBN-0001",
  "timestamp": 1710000000000
}
```

**Expected Response:**
```json
{
  "id": "unique-id",
  "status": "RECIBIDO"
}
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. System Won't Start
- Check if Docker is running: `docker --version`
- Check if ports are available: `netstat -an | grep 5555`
- Check dependencies: `pip install -r requirements.txt`

#### 2. Connection Refused
- Verify services are running: Check system status in menu
- Check firewall settings
- Verify network connectivity

#### 3. Test Failures
- Ensure sample data is generated (Option 1 in menu)
- Check if all services are running
- Review logs for error messages

#### 4. Performance Issues
- Reduce PS per site in load tests
- Check system resources (CPU, memory)
- Monitor logs for bottlenecks

### Getting Help

1. **Check System Status**: Use the status option in any menu
2. **View Logs**: Use the log monitoring features
3. **Review Documentation**: Check README.md and other docs
4. **Reset Data**: Regenerate sample data if needed

---

## 🎯 Quick Reference

### Essential Commands

| Action | Command |
|--------|---------|
| Start Python Menu | `python run_system.py` |
| Start Docker Menu | `./docker-scripts/menu.sh menu` |
| Quick Start | `./start.sh` |
| Monitor Logs | `python tools/log_monitor.py --interactive` |
| Check Status | `./docker-scripts/menu.sh status` |

### File Locations

| File | Location |
|------|----------|
| System Data | `data/siteA/`, `data/siteB/` |
| Test Results | `metrics/results.csv` |
| Performance Charts | `metrics/latency_vs_ps.png`, `metrics/throughput_vs_ps.png` |
| Configuration | `.env` files |

### Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| GC | 5555 | Central Manager |
| GC-PUB | 5556 | Publisher for Actors |
| AP | 5557 | Actor Préstamo |
| GA-A | 5560 | Storage Server A |
| GA-B | 5561 | Storage Server B |

---

## 📖 Additional Resources

- **README.md** - Project overview and architecture
- **DOCKER.md** - Docker-specific information
- **INTEGRATION_GUIDE.md** - Component integration details
- **specs/CONTRATO.md** - Technical specifications

---

This guide provides everything you need to use the distributed library system effectively. The menu-driven interfaces eliminate the need for manual command execution while providing full control over system operations.
