# Sebastián's Components - Distributed Library System

This document describes the components implemented by Sebastián for the distributed library system, following the contract specifications exactly.

## Components Overview

Sebastián has implemented the following components:

- **AR (Actor Renovación)**: Processes renovation requests via PUB/SUB
- **AD (Actor Devolución)**: Processes return requests via PUB/SUB  
- **AP (Actor Préstamo)**: Processes loan requests via REQ/REP
- **GA (Gestor de Almacenamiento)**: Storage server with replication
- **Tools**: Seed data generator, failover demo, debug subscriber

## Architecture

```
PS → GC → AR/AD (PUB/SUB) → GA
PS → GC → AP (REQ/REP) → GA
GA_A ↔ GA_B (Replication)
```

## Quick Start

### 1. Environment Setup

Create environment files for each site:

**Site A (.env.siteA):**
```bash
# GC Configuration
GC_BIND=tcp://0.0.0.0:5555
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION
GC_MODE=serial

# Connections to GC
GC_PUB_CONNECT=tcp://127.0.0.1:5556
AP_REQ_CONNECT=tcp://127.0.0.1:5557

# AP (Actor Préstamo)
AP_REP_BIND=tcp://0.0.0.0:5557

# GA (Site A)
GA_REP_BIND=tcp://0.0.0.0:5560
GA_HEALTH_REP_BIND=tcp://0.0.0.0:5564
GA_HEARTBEAT_PUB_BIND=tcp://0.0.0.0:5565
GA_HEARTBEAT_INTERVAL_MS=2000

# Replication (Site A publishes to 5562, subscribes to 5563)
GA_REPL_PUB_BIND=tcp://0.0.0.0:5562
GA_REPL_SUB_CONNECT=tcp://127.0.0.1:5563

# Data files
GA_DATA_DIR=./data/siteA
BOOKS_FILE=books.json
LOANS_FILE=loans.json
OPLOG_FILE=oplog.json
APPLIED_INDEX_FILE=applied_index.json
SNAPSHOT_INTERVAL_OPS=500
```

**Site B (.env.siteB):**
```bash
# Same as Site A but with inverted replication ports
GA_REPL_PUB_BIND=tcp://0.0.0.0:5563
GA_REPL_SUB_CONNECT=tcp://127.0.0.1:5562
GA_DATA_DIR=./data/siteB
```

### 2. Generate Seed Data

```bash
# Generate data for Site A
python tools/seed_data.py --data-dir ./data/siteA --site A

# Generate data for Site B  
python tools/seed_data.py --data-dir ./data/siteB --site B
```

### 3. Start Services

**Terminal 1 - GA_A (Site A):**
```bash
python -m ga.server --data-dir ./data/siteA --node-id A --pretty
```

**Terminal 2 - GA_B (Site B):**
```bash
python -m ga.server --data-dir ./data/siteB --node-id B --pretty
```

**Terminal 3 - Actor Préstamo (AP):**
```bash
python -m actors.prestamo --pretty
```

**Terminal 4 - Actor Renovación (AR):**
```bash
python -m actors.renovacion --pretty
```

**Terminal 5 - Actor Devolución (AD):**
```bash
python -m actors.devolucion --pretty
```

### 4. Test Integration

**Run failover demo:**
```bash
./tools/failover_demo.sh
```

**Debug PUB/SUB messages:**
```bash
# Subscribe to all topics
python tools/print_subscriber.py tcp://127.0.0.1:5556 --pretty

# Subscribe only to RENOVACION
python tools/print_subscriber.py tcp://127.0.0.1:5556 --topic RENOVACION --pretty
```

## Component Details

### Actors

#### AR (Actor Renovación)
- **File**: `actors/renovacion.py`
- **Protocol**: SUB to GC PUB/SUB
- **Topic**: `RENOVACION`
- **Function**: Processes renovation requests, calls `GA.renovar`

```bash
python -m actors.renovacion --pretty
```

#### AD (Actor Devolución)
- **File**: `actors/devolucion.py`
- **Protocol**: SUB to GC PUB/SUB
- **Topic**: `DEVOLUCION`
- **Function**: Processes return requests, calls `GA.devolver`

```bash
python -m actors.devolucion --pretty
```

#### AP (Actor Préstamo)
- **File**: `actors/prestamo.py`
- **Protocol**: REP server
- **Function**: Processes loan requests from GC, calls `GA.checkAndLoan`

```bash
python -m actors.prestamo --pretty
```

### GA (Gestor de Almacenamiento)

#### Server
- **File**: `ga/server.py`
- **Protocol**: REP server
- **Methods**: `renovar`, `devolver`, `checkAndLoan`
- **Features**: Storage, oplog, replication, health monitoring

```bash
python -m ga.server --data-dir ./data/siteA --node-id A --pretty
```

#### Storage
- **File**: `ga/storage.py`
- **Features**: Atomic read/write, business logic validation
- **Files**: `books.json`, `loans.json`

#### Oplog
- **File**: `ga/oplog.py`
- **Features**: Append-only log, idempotency, incremental reading

#### Replication
- **File**: `ga/replication.py`
- **Protocol**: PUB/SUB between GA nodes
- **Features**: Asynchronous replication, idempotency guarantees

#### Health
- **File**: `ga/health.py`
- **Features**: Heartbeat publishing, health check endpoint

## Business Rules

### Renovación (Renovation)
- Book must be loaned to the user
- Maximum 2 renovations per loan
- New due date = current due date + 7 days

### Devolución (Return)
- Book must be loaned to the user
- Mark book as available
- Remove loan record

### Préstamo (Loan)
- Book must be available
- Create loan with due date = today + 14 days
- Mark book as unavailable

## Data Format

### books.json
```json
[
  {
    "codigo": "ISBN-0001",
    "titulo": "El Quijote - Miguel de Cervantes",
    "disponible": true
  }
]
```

### loans.json
```json
[
  {
    "codigo": "ISBN-0001",
    "userId": "u-123",
    "dueDate": "2025-01-15",
    "renovaciones": 1
  }
]
```

### oplog.json
```json
[
  {
    "id": "uuid-unique",
    "op": "RENOVAR",
    "codigo": "ISBN-0001",
    "userId": "u-123",
    "dueDateNew": "2025-01-22",
    "ts": 1710000000000
  }
]
```

## Message Formats

### ActorMessage (GC → AR/AD)
```json
{
  "id": "uuid-unique",
  "sedeId": "A",
  "userId": "u-123",
  "libroCodigo": "ISBN-0001",
  "op": "RENOVAR",
  "dueDateNew": "2025-01-22"
}
```

### APRequest (GC → AP)
```json
{
  "id": "uuid-unique",
  "libroCodigo": "ISBN-0001",
  "userId": "u-123"
}
```

### APReply (AP → GC)
```json
{
  "ok": true,
  "reason": null,
  "metadata": {
    "dueDate": "2025-01-15"
  }
}
```

## Testing

### Manual Testing

**Test GA operations directly:**
```python
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5560')

# Test loan
request = {
    'method': 'checkAndLoan',
    'payload': {
        'id': 'test-1',
        'libroCodigo': 'ISBN-0001',
        'userId': 'u-1'
    }
}

socket.send_json(request)
response = socket.recv_json()
print(response)
```

**Test AP via GC:**
```python
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5557')

request = {
    'id': 'test-1',
    'libroCodigo': 'ISBN-0001',
    'userId': 'u-1'
}

socket.send_json(request)
response = socket.recv_json()
print(response)
```

### Integration Testing

**Run complete failover demo:**
```bash
./tools/failover_demo.sh
```

This script will:
1. Start GA_A and GA_B
2. Start all actors
3. Test initial operations
4. Test replication
5. Simulate GA_A failure
6. Test GA_B continues working
7. Restart GA_A
8. Test recovery and synchronization

## Logging

All components use standardized JSON logging:

```json
{
  "ts": 1710000000000,
  "proc": "AR|AD|AP|GA",
  "id": "uuid-unique",
  "op": "RENOVAR|DEVOLVER|PRESTAR",
  "stage": "recibido|enviado|aplicado|error",
  "detail": "Operation details"
}
```

Use `--pretty` flag for human-readable output.

## Troubleshooting

### Common Issues

**Connection refused:**
- Check if services are running
- Verify port configuration in .env
- Ensure no port conflicts

**Operations failing:**
- Check GA storage files exist
- Verify business rules (availability, renovation limits)
- Check oplog for idempotency issues

**Replication not working:**
- Verify GA nodes are configured with correct ports
- Check network connectivity between nodes
- Review replication logs

### Debug Tools

**Monitor PUB/SUB messages:**
```bash
python tools/print_subscriber.py tcp://127.0.0.1:5556 --pretty
```

**Check GA oplog:**
```bash
python -c "
import json
with open('./data/siteA/oplog.json') as f:
    print(json.dumps(json.load(f), indent=2))
"
```

**Test GA health:**
```bash
python -c "
import zmq
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5564')
socket.send_json({'status': 'check'})
response = socket.recv_json()
print(response)
"
```

## Integration with Alejandro's Components

Sebastián's components are designed to integrate seamlessly with Alejandro's GC and PS:

- **Topics**: Uses exact topic names (`RENOVACION`, `DEVOLUCION`)
- **Message formats**: Follows contract specifications exactly
- **Ports**: Configurable via environment variables
- **Logging**: Compatible JSON format
- **Error handling**: Graceful degradation and recovery

The system supports both development (with mock AP) and production (with real actors) modes.
