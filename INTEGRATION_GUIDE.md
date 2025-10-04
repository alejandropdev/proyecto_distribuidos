# Integration Guide - Sebastián's Components

This guide explains how to integrate Sebastián's components with Alejandro's existing system for the distributed library project.

## Overview

Sebastián has implemented the following components according to the contract:

- **AR (Actor Renovación)**: Processes renovation requests via PUB/SUB
- **AD (Actor Devolución)**: Processes return requests via PUB/SUB  
- **AP (Actor Préstamo)**: Processes loan requests via REQ/REP
- **GA (Gestor de Almacenamiento)**: Storage server with replication
- **Tools**: Seed data generator, failover demo, debug subscriber

## Quick Integration Steps

### 1. Environment Setup

Create environment files for each site:

**Site A (.env.siteA):**
```bash
# GC Configuration (Alejandro's)
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

**Run integration tests:**
```bash
python tools/integration_test.py
```

**Run failover demo:**
```bash
./tools/failover_demo.sh
```

**Debug PUB/SUB messages:**
```bash
python tools/print_subscriber.py tcp://127.0.0.1:5556 --pretty
```

## Message Flow

### Renovación Flow
```
PS → GC (REQ/REP) → GC publishes to RENOVACION topic → AR (SUB) → GA.renovar (REQ/REP)
```

### Devolución Flow
```
PS → GC (REQ/REP) → GC publishes to DEVOLUCION topic → AD (SUB) → GA.devolver (REQ/REP)
```

### Préstamo Flow
```
PS → GC (REQ/REP) → GC → AP (REQ/REP) → GA.checkAndLoan (REQ/REP) → AP → GC → PS
```

## Message Formats

### GC → AR/AD (PUB/SUB)
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

### GC → AP (REQ/REP)
```json
{
  "id": "uuid-unique",
  "libroCodigo": "ISBN-0001",
  "userId": "u-123"
}
```

### AP → GC (REQ/REP)
```json
{
  "ok": true,
  "reason": null,
  "metadata": {
    "dueDate": "2025-01-15"
  }
}
```

## Business Rules Implementation

### Renovación (Renovation)
- ✅ Book must be loaned to the user
- ✅ Maximum 2 renovations per loan
- ✅ New due date = current due date + 7 days

### Devolución (Return)
- ✅ Book must be loaned to the user
- ✅ Mark book as available
- ✅ Remove loan record

### Préstamo (Loan)
- ✅ Book must be available
- ✅ Create loan with due date = today + 14 days
- ✅ Mark book as unavailable

## Data Storage

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

## Replication

GA nodes replicate operations asynchronously using PUB/SUB:

- **GA_A**: Publishes on port 5562, subscribes on port 5563
- **GA_B**: Publishes on port 5563, subscribes on port 5562
- **Idempotency**: Operations with same ID are applied only once
- **Heartbeat**: Health monitoring every 2 seconds

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

**Run complete integration test:**
```bash
python tools/integration_test.py
```

**Run failover demo:**
```bash
./tools/failover_demo.sh
```

## Docker Integration

The components are designed to work with Alejandro's Docker setup:

**docker-compose.yml (Site B):**
```yaml
sitio-b:
  build: .
  container_name: sitio-b
  networks:
    - biblioteca-network
  ports:
    - "5557:5557"  # AP
    - "5560:5560"  # GA_A
    - "5561:5561"  # GA_B
  environment:
    - GC_PUB_CONNECT=tcp://sitio-a:5556
    - AP_REP_BIND=tcp://0.0.0.0:5557
    - GA_REP_BIND=tcp://0.0.0.0:5560
  volumes:
    - ./data:/app/data
  command: ["python", "-m", "ga.server", "--data-dir", "/app/data/siteA", "--node-id", "A"]
```

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

## Performance Considerations

- **Replication**: Asynchronous PUB/SUB for better performance
- **Oplog**: Periodic truncation to prevent unlimited growth
- **Storage**: Thread-safe operations with file locking
- **Health**: Lightweight heartbeat every 2 seconds

## Security Notes

- All operations are validated before execution
- Idempotency prevents duplicate operations
- File operations are atomic
- Network communication uses ZMQ security features

## Future Enhancements

- **Persistence**: Database backend instead of JSON files
- **Clustering**: Support for more than 2 GA nodes
- **Monitoring**: Metrics collection and alerting
- **Backup**: Automated backup and restore procedures

## Conclusion

Sebastián's components are fully compatible with Alejandro's system and follow the contract specifications exactly. The integration is seamless and provides a robust, distributed library management system with replication and failover capabilities.
