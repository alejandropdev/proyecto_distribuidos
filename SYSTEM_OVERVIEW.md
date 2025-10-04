# Distributed Library System - System Overview

## 🎯 Project Completion Summary

The distributed library system has been enhanced with **user-friendly menu interfaces** that eliminate the need for manual command execution. Users can now easily run and monitor the system through intuitive menus.

## 🚀 How to Use the System

### Quick Start Options

1. **Python Menu Interface (Recommended)**
   ```bash
   python run_system.py
   ```

2. **Docker Menu Interface**
   ```bash
   ./docker-scripts/menu.sh menu
   ```

3. **Quick Start Script**
   ```bash
   ./start.sh
   ```

## 📋 System Architecture

The system implements a distributed book lending system with the following components:

- **PS (Proceso Solicitante)**: Client processes that send requests
- **GC (Gestor Central)**: Central manager that routes requests
- **AR (Actor Renovación)**: Processes renewal requests via PUB/SUB
- **AD (Actor Devolución)**: Processes return requests via PUB/SUB  
- **AP (Actor Préstamo)**: Processes loan requests via REQ/REP
- **GA (Gestor de Almacenamiento)**: Storage server with replication

### Communication Patterns
- **PS ↔ GC**: REQ/REP (synchronous)
- **GC → AR/AD**: PUB/SUB (asynchronous)
- **GC ↔ AP**: REQ/REP (synchronous)
- **Actors ↔ GA**: REQ/REP (synchronous)
- **GA_A ↔ GA_B**: Replication (asynchronous)

## 🎮 Menu Features

### Python Menu Interface (`run_system.py`)

**Main Menu Options:**
1. **Setup & Data** - Generate sample data for both sites
2. **Docker Mode** - Run complete system using Docker
3. **Local Mode** - Run components locally without Docker
4. **Test System** - Test with sample requests
5. **Load Test** - Run performance tests
6. **Generate Charts** - Create performance charts
7. **View Logs** - Monitor system logs in real-time
8. **Stop System** - Stop all running services
9. **Exit** - Exit the program

**Features:**
- Real-time system status monitoring
- Interactive configuration
- Automatic dependency checking
- Graceful shutdown handling
- Comprehensive error handling

### Docker Menu Interface (`./docker-scripts/menu.sh`)

**Available Commands:**
- `start` - Start the system
- `stop` - Stop the system
- `restart` - Restart the system
- `status` - Show system status
- `logs` - View all logs
- `service` - View specific service logs
- `test` - Run system tests
- `charts` - Generate performance charts
- `cleanup` - Clean up containers and images
- `menu` - Show interactive menu

**Features:**
- Docker-specific operations
- Container management
- Real-time log viewing
- Service-specific monitoring

### Log Monitor (`tools/log_monitor.py`)

**Monitoring Options:**
1. **Monitor Docker Logs** - Real-time Docker container logs
2. **Monitor ZeroMQ Messages** - Real-time message monitoring
3. **Show Service Status** - Check all services
4. **View Recent Logs** - Show recent log entries

**Features:**
- Real-time log monitoring
- ZeroMQ message monitoring
- Service health checking
- Statistics and metrics
- Interactive interface

## 📊 Testing and Monitoring

### Automated Testing
- **System Test**: Basic functionality testing
- **Load Testing**: Configurable performance testing
- **Performance Metrics**: Response time, throughput, success rates

### Real-Time Monitoring
- Service status monitoring
- Log aggregation and filtering
- ZeroMQ message monitoring
- Performance statistics

### Results and Charts
- Test results saved to `metrics/results.csv`
- Performance charts generated in `metrics/` directory
- Real-time statistics display

## 🔧 Configuration

### Environment Variables
All system configuration is handled through environment variables:
- GC configuration (ports, topics)
- Connection endpoints
- Performance settings
- Data file locations

### Data Management
- Automatic sample data generation
- JSON-based data storage
- Replication between sites
- Operation logging

## 📚 Available Operations

### 1. PRESTAR (Loan a Book)
- Synchronous operation
- Availability checking
- Due date assignment
- Database updates

### 2. RENOVAR (Renew a Loan)
- Asynchronous operation
- PUB/SUB messaging
- Renewal limit checking
- Database updates

### 3. DEVOLVER (Return a Book)
- Asynchronous operation
- PUB/SUB messaging
- Immediate acknowledgment
- Database updates

## 🚨 Error Handling and Troubleshooting

### Built-in Diagnostics
- Dependency checking
- Service health monitoring
- Connection status verification
- Automatic error reporting

### Common Issues Resolved
- Port availability checking
- Service startup verification
- Network connectivity testing
- Resource monitoring

## 📖 Documentation

### User Guides
- **USAGE_GUIDE.md** - Comprehensive usage instructions
- **README.md** - Project overview with quick start
- **DOCKER.md** - Docker-specific information
- **INTEGRATION_GUIDE.md** - Component integration details

### Technical Documentation
- **specs/CONTRATO.md** - Technical specifications
- **SYSTEM_OVERVIEW.md** - This overview document

## 🎯 Key Benefits

### User Experience
- **No manual command execution required**
- **Intuitive menu-driven interfaces**
- **Real-time monitoring and feedback**
- **Comprehensive error handling**

### System Management
- **Automated setup and configuration**
- **Service health monitoring**
- **Performance testing and analysis**
- **Easy system startup and shutdown**

### Development and Testing
- **Integrated testing framework**
- **Performance metrics collection**
- **Real-time log monitoring**
- **Docker and local deployment options**

## 🚀 Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Choose your interface**:
   - Python Menu: `python run_system.py`
   - Docker Menu: `./docker-scripts/menu.sh menu`
   - Quick Start: `./start.sh`
3. **Follow the menu prompts** to set up and run the system
4. **Monitor and test** using the built-in tools

The system is now fully operational with user-friendly interfaces that make it easy to run, test, and monitor the distributed library system without requiring manual command execution.
