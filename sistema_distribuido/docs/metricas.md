# Métricas del Sistema Distribuido de Préstamo de Libros

## 📊 Definición de Métricas

### Métricas de Rendimiento

#### Latencia ACK (REQ/REP)
- **Definición**: Tiempo transcurrido entre envío de solicitud y recepción de ACK
- **Unidad**: Milisegundos (ms)
- **Valor objetivo**: < 500ms
- **Medición**: Promedio de todas las operaciones en `test_end_to_end.py`

#### Throughput de Operaciones
- **Definición**: Número de operaciones procesadas por segundo
- **Unidad**: Operaciones/segundo (ops/s)
- **Valor esperado**: ~1 ops/s (limitado por sleep de 1s en PS)
- **Medición**: Conteo de operaciones en logs del GC

#### Tiempo de Procesamiento Asíncrono
- **Definición**: Tiempo entre ACK y actualización de base de datos
- **Unidad**: Segundos (s)
- **Valor esperado**: 1-3 segundos
- **Medición**: Diferencia temporal entre logs de GC y actores

### Métricas de Calidad

#### Tasa de Éxito
- **Definición**: Porcentaje de operaciones procesadas exitosamente
- **Unidad**: Porcentaje (%)
- **Valor objetivo**: 100%
- **Cálculo**: `(operaciones_ok / total_operaciones) * 100`

#### Tasa de Recepción PUB/SUB
- **Definición**: Porcentaje de eventos recibidos vs. enviados
- **Unidad**: Porcentaje (%)
- **Valor objetivo**: 100%
- **Medición**: En `test_pubsub_visibility.py`

#### Tasa de Actualización de BD
- **Definición**: Porcentaje de operaciones que actualizan la base de datos
- **Unidad**: Porcentaje (%)
- **Valor objetivo**: 100%
- **Medición**: Verificación de cambios en `libros.json`

### Métricas de Distribución

#### Número de Procesos
- **Definición**: Cantidad total de procesos en el sistema
- **Valor mínimo**: 3 (GC + 2 Actores)
- **Valor típico**: 4 (incluyendo PS)
- **Medición**: Conteo de contenedores en `docker ps`

#### Número de Computadores
- **Definición**: Cantidad de IPs únicas en la red Docker
- **Valor mínimo**: 2
- **Valor típico**: 4 (uno por contenedor)
- **Medición**: `show_ips.sh` cuenta IPs distintas

#### Distribución de Carga
- **Definición**: Balance de operaciones entre actores
- **Métrica**: Ratio de devoluciones vs. renovaciones
- **Valor esperado**: Depende del archivo de solicitudes
- **Medición**: Conteo en logs de actores

## 🔧 Cómo Se Recolectan las Métricas

### Automatización
Las métricas se recolectan automáticamente mediante:

1. **Scripts de orquestación** (`run_tests.sh`, `collect_evidence.sh`)
2. **Tests pytest** con mediciones integradas
3. **Análisis de logs** con grep/awk
4. **Monitoreo de archivos** con `wait_for_file_change`

### Fuentes de Datos

#### Logs de Servicios
```bash
# Contar operaciones en GC
grep -c "Operación.*procesada" logs/evidence/gc_logs.txt

# Contar publicaciones por tema
grep -c "Topic: devolucion" logs/evidence/gc_logs.txt
grep -c "Topic: renovacion" logs/evidence/gc_logs.txt

# Contar errores
grep -c "ERROR" logs/evidence/gc_logs.txt
```

#### Archivos de Estado
```bash
# Verificar cambios en BD
diff -u logs/evidence/libros_before.json logs/evidence/libros_after.json

# Contar solicitudes en archivo
wc -l data/solicitudes.txt
```

#### Tests Automatizados
```python
# Medición de latencia en tests
start_time = time.time()
status, ack_ms = TestUtils.send_req(gc_endpoint, payload)
end_time = time.time()
latency = (end_time - start_time) * 1000
```

### Herramientas de Análisis

#### Scripts Personalizados
- `show_ips.sh`: IPs y distribución de procesos
- `wait_for_gc.sh`: Tiempo de inicialización
- `collect_evidence.sh`: Recolección centralizada

#### Comandos Docker
```bash
# Estado de contenedores
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs con timestamps
docker logs --timestamps gc

# Estadísticas de red
docker network inspect red_distribuida
```

## 📈 Análisis de Métricas

### Latencia ACK
```bash
# Extraer tiempos de ACK de logs
grep "ACK recibido en" logs/test_end_to_end.txt | \
  grep -o "[0-9]\+\.[0-9]\+ms" | \
  sort -n
```

**Interpretación**:
- < 100ms: Excelente
- 100-500ms: Bueno
- > 500ms: Requiere investigación

### Throughput
```bash
# Calcular operaciones por segundo
total_ops=$(grep -c "Operación.*procesada" logs/evidence/gc_logs.txt)
tiempo_total=$(grep "Operación #1" logs/evidence/gc_logs.txt | head -1 | cut -d' ' -f1)
# [cálculo de diferencia temporal]
```

**Interpretación**:
- 1 ops/s: Esperado (limitado por sleep)
- < 1 ops/s: Posible problema de rendimiento
- > 1 ops/s: Inesperado, verificar configuración

### Tasa de Éxito
```bash
# Calcular tasa de éxito
ops_ok=$(grep -c "Solicitud procesada exitosamente" logs/evidence/ps_logs.txt)
ops_total=$(grep -c "Solicitud #" logs/evidence/ps_logs.txt)
tasa_exito=$((ops_ok * 100 / ops_total))
echo "Tasa de éxito: $tasa_exito%"
```

**Interpretación**:
- 100%: Perfecto
- 95-99%: Aceptable
- < 95%: Requiere investigación

## 📊 Dashboard de Métricas

### Métricas en Tiempo Real
```bash
# Monitoreo continuo
watch -n 1 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

### Reporte de Métricas
```bash
# Generar reporte completo
./scripts/collect_evidence.sh
cat logs/evidence/metricas.txt
```

### Alertas Automáticas
```bash
# Verificar métricas críticas
if [ $(grep -c "ERROR" logs/evidence/gc_logs.txt) -gt 0 ]; then
    echo "⚠️ ALERTA: Errores detectados en GC"
fi

if [ $(grep -c "IP:" logs/evidence/ips.txt) -lt 2 ]; then
    echo "⚠️ ALERTA: Menos de 2 computadores detectados"
fi
```

## 🎯 Objetivos de Rendimiento

### Objetivos Primarios
- **Latencia ACK**: < 500ms (100% de operaciones)
- **Tasa de éxito**: 100% (0 errores)
- **Distribución**: ≥2 computadores (IPs distintas)
- **Funcionalidad**: 100% de operaciones procesadas

### Objetivos Secundarios
- **Throughput**: 1 ops/s (limitado por diseño)
- **Tiempo de inicialización**: < 30 segundos
- **Uso de memoria**: < 100MB por contenedor
- **Disponibilidad**: 99.9% (sin crashes)

### Límites de Degradación
- **Latencia ACK**: > 1000ms (crítico)
- **Tasa de éxito**: < 95% (crítico)
- **Pérdida de eventos**: > 0% (crítico)
- **Crashes**: > 0 (crítico)

## 📋 Checklist de Métricas

### Antes de la Prueba
- [ ] Servicios levantados correctamente
- [ ] Red Docker configurada
- [ ] Archivos de datos disponibles
- [ ] Logs limpios

### Durante la Prueba
- [ ] Latencia ACK medida
- [ ] Eventos PUB/SUB recibidos
- [ ] Base de datos actualizada
- [ ] Sin errores críticos

### Después de la Prueba
- [ ] Métricas recolectadas
- [ ] Evidencias guardadas
- [ ] Reporte generado
- [ ] Objetivos verificados

## 🔍 Troubleshooting de Métricas

### Latencia Alta
**Posibles causas**:
- Red Docker lenta
- GC sobrecargado
- Problemas de DNS

**Soluciones**:
- Verificar conectividad de red
- Revisar logs de GC
- Reiniciar contenedores

### Tasa de Éxito Baja
**Posibles causas**:
- Errores en procesamiento
- Timeouts de red
- Problemas de sincronización

**Soluciones**:
- Revisar logs de errores
- Aumentar timeouts
- Verificar configuración

### Pérdida de Eventos
**Posibles causas**:
- Slow joiner de ZeroMQ
- Problemas de suscripción
- GC no publicando

**Soluciones**:
- Aumentar tiempo de espera
- Verificar suscripciones
- Revisar logs de GC

## 📈 Mejoras Futuras

### Métricas Adicionales
- Latencia p50, p95, p99
- Uso de CPU por contenedor
- Ancho de banda de red
- Tiempo de procesamiento por actor

### Herramientas de Monitoreo
- Prometheus + Grafana
- ELK Stack para logs
- Jaeger para tracing distribuido
- Custom dashboards

### Alertas Automáticas
- Slack/Email notifications
- Health checks automáticos
- Auto-recovery de servicios
- Escalado automático
