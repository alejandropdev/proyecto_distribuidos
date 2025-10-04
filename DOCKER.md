# Docker Configuration for Distributed Library System

This Docker setup simulates a distributed environment with multiple machines on a single computer, allowing Alejandro and Sebastián to develop and test their components independently.

## Architecture Overview

The Docker setup creates three main containers:

1. **Site A (sitio-a)**: Alejandro's components (GC + PS)
2. **Site B (sitio-b)**: Sebastián's components (AR, AD, AP, GA)
3. **Load Generator**: Alejandro's load testing tools

## Quick Start

### 1. Build the Docker Image

```bash
./docker-scripts/build.sh
```

### 2. Development Environment (Alejandro only)

```bash
# Start development environment with mock AP
./docker-scripts/dev.sh

# Test PS client
./docker-scripts/test.sh

# Run load test
./docker-scripts/load.sh

# View logs
./docker-scripts/logs.sh

# Stop containers
./docker-scripts/stop.sh
```

### 3. Production Environment (with Sebastián's components)

```bash
# Start full environment
docker-compose up -d

# Run load test
docker-compose run --rm load-generator

# Stop all
docker-compose down
```

## Container Details

### Site A (Alejandro's Components)

- **Container**: `sitio-a` / `sitio-a-dev`
- **Ports**: 
  - 5555: GC REQ/REP (PS → GC)
  - 5556: GC PUB/SUB (GC → Actors)
- **Services**: GC Server, PS Clients
- **Environment Variables**:
  - `GC_BIND=tcp://0.0.0.0:5555`
  - `GC_PUB_BIND=tcp://0.0.0.0:5556`
  - `AP_REQ_CONNECT=tcp://sitio-b:5557`

### Site B (Sebastián's Components)

- **Container**: `sitio-b` / `sitio-b-dev`
- **Ports**:
  - 5557: AP REQ/REP (GC → AP)
  - 5560: GA_A (Actor → GA_A)
  - 5561: GA_B (Actor → GA_B)
- **Services**: AR, AD, AP, GA_A, GA_B
- **Environment Variables**:
  - `GC_PUB_CONNECT=tcp://sitio-a:5556`
  - `AP_REP_BIND=tcp://0.0.0.0:5557`

### Load Generator

- **Container**: `load-generator` / `load-test`
- **Services**: PS spawner, metrics collection
- **Output**: `metrics/results.csv`

## Network Configuration

All containers communicate through a custom Docker network (`biblioteca-network`) with subnet `172.20.0.0/16`.

### Internal Communication

- **PS → GC**: `tcp://sitio-a:5555`
- **GC → Actors**: `tcp://sitio-a:5556` (PUB/SUB)
- **GC → AP**: `tcp://sitio-b:5557`
- **Actors → GA**: `tcp://sitio-b:5560` or `tcp://sitio-b:5561`

## Development Workflow

### For Alejandro (Testing without Sebastián)

1. **Start development environment**:
   ```bash
   ./docker-scripts/dev.sh
   ```

2. **Test individual PS client**:
   ```bash
   ./docker-scripts/test.sh
   ```

3. **Run performance tests**:
   ```bash
   ./docker-scripts/load.sh
   ```

4. **Generate charts**:
   ```bash
   python tools/charts.py --csv metrics/results.csv --outdir metrics/
   ```

### For Sebastián (Integration Testing)

1. **Replace Site B command** in `docker-compose.yml`:
   ```yaml
   sitio-b:
     command: ["python", "-m", "sebastian.server"]  # Replace with actual command
   ```

2. **Start full environment**:
   ```bash
   docker-compose up -d
   ```

3. **Test integration**:
   ```bash
   docker-compose run --rm load-generator
   ```

## Environment Variables

### Site A (Alejandro)

```bash
GC_BIND=tcp://0.0.0.0:5555
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION
AP_REQ_CONNECT=tcp://sitio-b:5557
GC_MODE=serial
METRICS_CSV=metrics/results.csv
MEASUREMENT_WINDOW_SEC=120
```

### Site B (Sebastián)

```bash
GC_PUB_CONNECT=tcp://sitio-a:5556
AP_REP_BIND=tcp://0.0.0.0:5557
GA_A_REP_BIND=tcp://0.0.0.0:5560
GA_B_REP_BIND=tcp://0.0.0.0:5561
```

## Volume Mounts

- `./data:/app/data` - Shared request files
- `./metrics:/app/metrics` - Shared metrics output

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs sitio-a-dev

# Rebuild image
docker-compose build sitio-a-dev
```

### Connection Issues

```bash
# Check network connectivity
docker exec sitio-a-dev ping sitio-b-dev

# Check port binding
docker port sitio-a-dev
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check container logs
docker logs sitio-a-dev -f
```

## Customization

### Adding New Services

1. **Add to docker-compose.yml**:
   ```yaml
   new-service:
     build: .
     container_name: new-service
     networks:
       - biblioteca-network
     ports:
       - "5558:5558"
   ```

2. **Update environment variables** in other services

3. **Restart environment**:
   ```bash
   docker-compose down && docker-compose up -d
   ```

### Changing Network Configuration

Edit `docker-compose.yml`:
```yaml
networks:
  biblioteca-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16  # Change subnet
```

## Integration with Sebastián

When Sebastián is ready to integrate:

1. **Share the docker-compose.yml** file
2. **Sebastián replaces the Site B command** with his actual services
3. **Test integration** using the load generator
4. **Debug** using Docker logs and network inspection

This setup allows both developers to work independently while maintaining the distributed architecture specified in the contract.
