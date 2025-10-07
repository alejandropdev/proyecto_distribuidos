# Plan de Pruebas - Sistema Distribuido de Préstamo de Libros

## Objetivo

Validar que el sistema distribuido cumple con todos los requisitos de la **Entrega #1** del proyecto de sistemas distribuidos, incluyendo comunicación ZeroMQ, distribución de procesos y operaciones end-to-end.

## Tests Implementados

### 1. Test End-to-End Básico (`test_end_to_end.py`)

**Objetivo**: Validar comunicación REQ/REP, PUB/SUB y actualización de base de datos sin usar PS.

**Criterios validados**:
- ✅ Comunicación REQ/REP entre tester y GC con ACK inmediato (< 500ms)
- ✅ Publicación asíncrona de eventos via PUB/SUB
- ✅ Actualización correcta de `libros.json` por actores
- ✅ Manejo graceful de operaciones inválidas

**Operaciones probadas**:
- Devolución de libro (incrementa `ejemplares_disponibles`)
- Renovación de libro (actualiza `fecha_devolucion` con +7 días)
- Operación inválida (debe responder ERROR sin crashear)

### 2. Test Pub/Sub Visibilidad (`test_pubsub_visibility.py`)

**Objetivo**: Verificar que los eventos se publiquen correctamente en los topics correspondientes.

**Criterios validados**:
- ✅ Suscripción a topics "devolucion" y "renovacion"
- ✅ Recepción de eventos con estructura correcta
- ✅ Validación de timestamps y campos requeridos
- ✅ Tasa de recepción 100% (sin pérdida de eventos)

**Escenarios probados**:
- Suscripción individual a cada topic
- Suscripción simultánea a múltiples topics
- Validación de estructura de eventos

### 3. Test Workload con Archivo (`test_file_workload.py`)

**Objetivo**: Validar procesamiento completo del archivo de solicitudes por PS.

**Criterios validados**:
- ✅ PS lee y procesa todas las líneas del archivo
- ✅ GC recibe y procesa todas las solicitudes
- ✅ Publicaciones por tema coinciden con conteo por tipo
- ✅ Base de datos se actualiza según operaciones procesadas

**Validaciones**:
- Conteo de solicitudes enviadas vs. líneas en archivo
- Análisis de logs de PS y GC
- Verificación de cambios en `libros.json`

## Checklist de Aceptación

### Requisitos de Distribución
- [ ] **≥3 procesos en ≥2 computadores**: Verificado por `show_ips.sh` - debe mostrar al menos 2 IPs distintas
- [ ] **Comunicación TCP entre contenedores**: Validado por resolución DNS (`gc:5001`, `gc:5002`)
- [ ] **Cada contenedor con IP propia**: Confirmado por `docker inspect` en cada servicio

### Requisitos de Comunicación
- [ ] **REQ/REP (PS→GC) con ACK inmediato**: Validado en `test_end_to_end.py` - ACK < 500ms
- [ ] **PUB/SUB (GC→Actores) por temas**: Validado en `test_pubsub_visibility.py` - topics "devolucion" y "renovacion"
- [ ] **Comunicación asíncrona**: Confirmado por separación temporal entre ACK y actualización de BD

### Requisitos Funcionales
- [ ] **Operaciones RENOVACIÓN y DEVOLUCIÓN**: Validadas en `test_end_to_end.py`
- [ ] **Actualización de `libros.json`**: Verificada por cambios en ejemplares y fechas
- [ ] **Archivo de carga procesado por PS**: Validado en `test_file_workload.py`
- [ ] **Manejo de errores graceful**: Confirmado por respuesta ERROR a operaciones inválidas

### Requisitos de Observabilidad
- [ ] **Logs con timestamps**: Verificado en todos los servicios
- [ ] **Contadores de operaciones**: Implementados en GC y PS
- [ ] **Métricas de rendimiento**: Latencia ACK medida en tests

## Cómo Ejecutar las Pruebas

### Opción 1: Suite Completa (Recomendado)
```bash
make test
```

### Opción 2: Pasos Individuales
```bash
# 1. Levantar servicios básicos
make up

# 2. Ejecutar tests
docker compose run --rm tester python -m pytest -v tests/

# 3. Recolectar evidencias
make evidence
```

### Opción 3: Tests Específicos
```bash
# Test end-to-end únicamente
docker compose run --rm tester python -m pytest -v tests/test_end_to_end.py

# Test pub/sub únicamente
docker compose run --rm tester python -m pytest -v tests/test_pubsub_visibility.py

# Test workload únicamente
docker compose --profile demo up -d ps
docker compose run --rm tester python -m pytest -v tests/test_file_workload.py
```

## Criterios de Éxito

### Test End-to-End
- ✅ ACK recibido en < 500ms para todas las operaciones
- ✅ Eventos PUB/SUB recibidos correctamente
- ✅ Base de datos actualizada según operación
- ✅ Operaciones inválidas manejadas sin crash

### Test Pub/Sub Visibilidad
- ✅ Tasa de recepción 100% (sin pérdida de eventos)
- ✅ Estructura de eventos correcta
- ✅ Timestamps válidos y recientes
- ✅ Suscripción a múltiples topics funcional

### Test Workload con Archivo
- ✅ Todas las líneas del archivo procesadas
- ✅ Logs de PS y GC coherentes
- ✅ Publicaciones por tema correctas
- ✅ Cambios en base de datos detectados

## Interpretación de Resultados

### Logs de Pruebas
- **Ubicación**: `logs/test_*.txt`
- **Contenido**: Resultados detallados de cada test
- **Formato**: Timestamp, métricas, estado PASSED/FAILED

### Evidencias Recolectadas
- **Ubicación**: `logs/evidence/`
- **Contenido**: Logs de servicios, IPs, diffs de BD, métricas
- **Resumen**: `logs/evidence/resumen.txt`

### Métricas Principales
- **Latencia ACK**: Tiempo promedio de respuesta REQ/REP
- **Operaciones procesadas**: Total de solicitudes manejadas
- **Tasa de éxito**: Porcentaje de operaciones exitosas
- **IPs únicas**: Número de "computadores" en el sistema

## Troubleshooting

### Problemas Comunes

1. **GC no responde**
   - Verificar que `docker compose up -d gc` se ejecutó
   - Revisar logs: `docker logs gc`
   - Ejecutar: `./scripts/wait_for_gc.sh`

2. **Tests fallan por timeout**
   - Verificar que todos los servicios están corriendo
   - Aumentar timeouts en tests si es necesario
   - Revisar conectividad de red Docker

3. **PS no procesa archivo**
   - Verificar que PS está en perfil demo: `docker compose --profile demo up -d ps`
   - Revisar archivo de solicitudes: `cat data/solicitudes.txt`
   - Verificar logs: `docker logs ps`

4. **Base de datos no se actualiza**
   - Verificar que actores están corriendo
   - Revisar logs de actores: `docker logs actor_dev actor_ren`
   - Verificar permisos de escritura en `data/`

### Comandos de Diagnóstico

```bash
# Estado de contenedores
docker compose ps

# IPs internas
./scripts/show_ips.sh

# Logs de todos los servicios
make logs

# Verificar conectividad
docker compose run --rm tester python -c "import zmq; print('ZeroMQ OK')"
```

## Métricas de Rendimiento

### Latencia Esperada
- **ACK REQ/REP**: < 500ms
- **Procesamiento asíncrono**: 1-3 segundos
- **Actualización BD**: 1-2 segundos después del evento

### Throughput Esperado
- **Solicitudes por segundo**: 1 (con sleep de 1s en PS)
- **Eventos por segundo**: 1-2 (dependiendo del tipo)
- **Actualizaciones BD**: 1 por operación

### Recursos del Sistema
- **Memoria por contenedor**: ~50-100MB
- **CPU**: Bajo uso (sistema I/O bound)
- **Red**: Tráfico mínimo (mensajes JSON pequeños)

## Conclusión

La suite de pruebas valida exhaustivamente todos los requisitos de la Entrega #1:

1. **Distribución**: 4 contenedores con IPs distintas
2. **Comunicación**: REQ/REP y PUB/SUB funcionando correctamente
3. **Funcionalidad**: Operaciones RENOVACIÓN y DEVOLUCIÓN end-to-end
4. **Observabilidad**: Logs detallados y métricas de rendimiento
5. **Robustez**: Manejo graceful de errores

**Resultado esperado**: Todos los tests PASSED, evidencias recolectadas, requisitos verificados.
