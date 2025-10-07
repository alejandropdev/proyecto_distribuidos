# Plantilla de Evidencias - Sistema Distribuido de Préstamo de Libros

## Instrucciones

Esta plantilla debe completarse con las evidencias recolectadas durante la ejecución de la suite de pruebas. Todas las capturas y reportes deben pegarse en las secciones correspondientes.

## Estado de Contenedores

### Docker PS
```bash
docker ps
```
**Pegar salida aquí:**
```
[PEGAR SALIDA DE docker ps]
```

### Docker Compose PS
```bash
docker compose ps
```
**Pegar salida aquí:**
```
[PEGAR SALIDA DE docker compose ps]
```

## IPs Internas por Contenedor

### Comando ejecutado
```bash
./scripts/show_ips.sh
```

**Pegar salida aquí:**
```
[PEGAR SALIDA DE show_ips.sh]
```

**Verificación**: ¿Se detectaron ≥2 IPs distintas? [ ] SÍ [ ] NO

## Logs de Servicios

### Gestor de Carga (GC)
```bash
docker logs gc --tail=50
```
**Pegar salida aquí:**
```
[PEGAR LOGS DEL GC]
```

### Actor de Devolución
```bash
docker logs actor_dev --tail=30
```
**Pegar salida aquí:**
```
[PEGAR LOGS DEL ACTOR DE DEVOLUCIÓN]
```

### Actor de Renovación
```bash
docker logs actor_ren --tail=30
```
**Pegar salida aquí:**
```
[PEGAR LOGS DEL ACTOR DE RENOVACIÓN]
```

### Proceso Solicitante (PS)
```bash
docker logs ps --tail=50
```
**Pegar salida aquí:**
```
[PEGAR LOGS DEL PS]
```

## Diferencias en Base de Datos

### Estado Inicial (libros_before.json)
```json
[PEGAR CONTENIDO DE logs/evidence/libros_before.json]
```

### Estado Final (libros_after.json)
```json
[PEGAR CONTENIDO DE logs/evidence/libros_after.json]
```

### Diferencias (libros.diff)
```bash
cat logs/evidence/libros.diff
```
**Pegar salida aquí:**
```
[PEGAR DIFERENCIAS]
```

## Resultados de Tests

### Test End-to-End
```bash
docker compose run --rm tester python -m pytest -v tests/test_end_to_end.py
```
**Pegar salida aquí:**
```
[PEGAR RESULTADO DEL TEST]
```

**Estado**: [ ] PASSED [ ] FAILED

### Test Pub/Sub Visibilidad
```bash
docker compose run --rm tester python -m pytest -v tests/test_pubsub_visibility.py
```
**Pegar salida aquí:**
```
[PEGAR RESULTADO DEL TEST]
```

**Estado**: [ ] PASSED [ ] FAILED

### Test Workload con Archivo
```bash
docker compose run --rm tester python -m pytest -v tests/test_file_workload.py
```
**Pegar salida aquí:**
```
[PEGAR RESULTADO DEL TEST]
```

**Estado**: [ ] PASSED [ ] FAILED

## Métricas del Sistema

### Archivo de Métricas
```bash
cat logs/evidence/metricas.txt
```
**Pegar salida aquí:**
```
[PEGAR MÉTRICAS]
```

### Resumen de Pruebas
```bash
cat logs/resumen_pruebas.txt
```
**Pegar salida aquí:**
```
[PEGAR RESUMEN]
```

## Análisis de Comunicación

### Secuencia REQ/REP (PS → GC)
**Ejemplo de solicitud:**
```json
{
  "op": "RENOVACION",
  "libro_id": "L001",
  "usuario_id": "U001",
  "sede": "SEDE_1"
}
```

**Ejemplo de respuesta:**
```json
{
  "status": "OK",
  "message": "Recibido. Procesando...",
  "operacion": "RENOVACION",
  "libro_id": "L001"
}
```

**Tiempo de ACK medido**: _____ ms

### Secuencia PUB/SUB (GC → Actores)
**Ejemplo de evento de renovación:**
```json
{
  "operacion": "RENOVACION",
  "libro_id": "L001",
  "usuario_id": "U001",
  "sede": "SEDE_1",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "nueva_fecha_devolucion": "2025-02-03"
}
```

**Ejemplo de evento de devolución:**
```json
{
  "operacion": "DEVOLUCION",
  "libro_id": "L002",
  "usuario_id": "U002",
  "sede": "SEDE_1",
  "timestamp": "2025-01-27T10:31:00.000Z"
}
```

## Checklist de Verificación

### Requisitos de Distribución
- [ ] **≥3 procesos**: Confirmado por `docker ps` (GC + 2 Actores + PS)
- [ ] **≥2 computadores**: Confirmado por IPs distintas en `show_ips.sh`
- [ ] **Comunicación TCP**: Confirmado por resolución DNS entre contenedores

### Requisitos de Comunicación
- [ ] **REQ/REP funcional**: Confirmado por ACK inmediato en logs
- [ ] **PUB/SUB funcional**: Confirmado por recepción de eventos
- [ ] **Topics correctos**: "devolucion" y "renovacion" funcionando

### Requisitos Funcionales
- [ ] **RENOVACIÓN funciona**: Confirmado por actualización de fecha en BD
- [ ] **DEVOLUCIÓN funciona**: Confirmado por incremento de ejemplares
- [ ] **Archivo procesado**: Confirmado por conteo de solicitudes en logs
- [ ] **Manejo de errores**: Confirmado por respuesta ERROR a operaciones inválidas

### Requisitos de Observabilidad
- [ ] **Logs con timestamps**: Confirmado en todos los servicios
- [ ] **Contadores presentes**: Confirmado en logs de GC y PS
- [ ] **Métricas recolectadas**: Confirmado en archivo de métricas

## Resumen Ejecutivo

### Estado General
- **Tests ejecutados**: _____ / 3
- **Tests pasados**: _____ / 3
- **Tests fallidos**: _____ / 3

### Criterios Cumplidos
- **Distribución**: [ ] SÍ [ ] NO
- **Comunicación**: [ ] SÍ [ ] NO
- **Funcionalidad**: [ ] SÍ [ ] NO
- **Observabilidad**: [ ] SÍ [ ] NO

### Observaciones
```
[ESCRIBIR OBSERVACIONES RELEVANTES]
```

### Problemas Encontrados
```
[ESCRIBIR PROBLEMAS O INCIDENTES]
```

### Recomendaciones
```
[ESCRIBIR RECOMENDACIONES PARA MEJORAS]
```

## Archivos de Evidencia

### Ubicación de Evidencias
- **Directorio principal**: `logs/evidence/`
- **Logs de tests**: `logs/test_*.txt`
- **Resumen general**: `logs/resumen_pruebas.txt`

### Archivos Incluidos
- [ ] `containers_docker_ps.txt`
- [ ] `containers_compose_ps.txt`
- [ ] `ips.txt`
- [ ] `gc_logs.txt`
- [ ] `actor_dev_logs.txt`
- [ ] `actor_ren_logs.txt`
- [ ] `ps_logs.txt`
- [ ] `libros_before.json`
- [ ] `libros_after.json`
- [ ] `libros.diff`
- [ ] `solicitudes.txt`
- [ ] `metricas.txt`
- [ ] `resumen.txt`

## Conclusión

**¿Se cumplen todos los requisitos de la Entrega #1?**
[ ] SÍ - Sistema distribuido funcional y completo
[ ] NO - Requiere correcciones adicionales

**Fecha de verificación**: _________________

**Verificado por**: _________________

**Comentarios finales**:
```
[ESCRIBIR COMENTARIOS FINALES]
```
