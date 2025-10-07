#!/bin/bash
# -*- coding: utf-8 -*-
# collect_evidence.sh - Recolecta evidencias del sistema

set -euo pipefail

# Configuración
LOGS_DIR="./logs"
EVIDENCE_DIR="$LOGS_DIR/evidence"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Recolectando evidencias del sistema..."
echo "Timestamp: $(date)"

# Crear directorio de evidencias
mkdir -p "$EVIDENCE_DIR"

# Función para loggear con timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_with_timestamp "Iniciando recolección de evidencias..."

# 1. Estado de contenedores
log_with_timestamp "Recolectando estado de contenedores..."
docker ps > "$EVIDENCE_DIR/containers_docker_ps.txt" 2>&1 || true
docker compose ps > "$EVIDENCE_DIR/containers_compose_ps.txt" 2>&1 || true

# 2. IPs internas
log_with_timestamp "Recolectando IPs internas..."
if [ -f "$LOGS_DIR/ips.txt" ]; then
    cp "$LOGS_DIR/ips.txt" "$EVIDENCE_DIR/ips.txt"
else
    echo "WARNING: Archivo de IPs no encontrado, ejecutando show_ips.sh..."
    ./scripts/show_ips.sh || true
    cp "$LOGS_DIR/ips.txt" "$EVIDENCE_DIR/ips.txt" 2>/dev/null || true
fi

# 3. Logs de servicios
log_with_timestamp "Recolectando logs de servicios..."

# Logs del GC
if docker ps --format "{{.Names}}" | grep -q "^gc$"; then
    docker logs gc > "$EVIDENCE_DIR/gc_logs.txt" 2>&1 || true
    log_with_timestamp "Logs del GC recolectados"
else
    echo "WARNING: GC no está corriendo" > "$EVIDENCE_DIR/gc_logs.txt"
fi

# Logs del Actor de Devolución
if docker ps --format "{{.Names}}" | grep -q "^actor_dev$"; then
    docker logs actor_dev > "$EVIDENCE_DIR/actor_dev_logs.txt" 2>&1 || true
    log_with_timestamp "Logs del Actor de Devolución recolectados"
else
    echo "WARNING: Actor de Devolución no está corriendo" > "$EVIDENCE_DIR/actor_dev_logs.txt"
fi

# Logs del Actor de Renovación
if docker ps --format "{{.Names}}" | grep -q "^actor_ren$"; then
    docker logs actor_ren > "$EVIDENCE_DIR/actor_ren_logs.txt" 2>&1 || true
    log_with_timestamp "Logs del Actor de Renovación recolectados"
else
    echo "WARNING: Actor de Renovación no está corriendo" > "$EVIDENCE_DIR/actor_ren_logs.txt"
fi

# Logs del PS (si está corriendo)
if docker ps --format "{{.Names}}" | grep -q "^ps$"; then
    docker logs ps > "$EVIDENCE_DIR/ps_logs.txt" 2>&1 || true
    log_with_timestamp "Logs del PS recolectados"
else
    echo "WARNING: PS no está corriendo" > "$EVIDENCE_DIR/ps_logs.txt"
fi

# 4. Estado de la base de datos
log_with_timestamp "Recolectando estado de la base de datos..."

# Crear snapshot antes si no existe
if [ ! -f "$EVIDENCE_DIR/libros_before.json" ]; then
    if [ -f "./data/libros.json" ]; then
        cp "./data/libros.json" "$EVIDENCE_DIR/libros_before.json"
        log_with_timestamp "Snapshot 'antes' creado"
    else
        echo "[]" > "$EVIDENCE_DIR/libros_before.json"
        log_with_timestamp "Snapshot 'antes' vacío creado"
    fi
fi

# Estado actual
if [ -f "./data/libros.json" ]; then
    cp "./data/libros.json" "$EVIDENCE_DIR/libros_after.json"
    log_with_timestamp "Estado actual de libros.json recolectado"
else
    echo "[]" > "$EVIDENCE_DIR/libros_after.json"
    log_with_timestamp "WARNING: Archivo libros.json no encontrado"
fi

# 5. Diferencias en la base de datos
log_with_timestamp "Generando diferencias de libros.json..."
if [ -f "$EVIDENCE_DIR/libros_before.json" ] && [ -f "$EVIDENCE_DIR/libros_after.json" ]; then
    diff -u "$EVIDENCE_DIR/libros_before.json" "$EVIDENCE_DIR/libros_after.json" > "$EVIDENCE_DIR/libros.diff" || true
    log_with_timestamp "Diferencias generadas"
else
    echo "WARNING: No se pudieron generar diferencias" > "$EVIDENCE_DIR/libros.diff"
fi

# 6. Archivo de solicitudes
log_with_timestamp "Recolectando archivo de solicitudes..."
if [ -f "./data/solicitudes.txt" ]; then
    cp "./data/solicitudes.txt" "$EVIDENCE_DIR/solicitudes.txt"
    log_with_timestamp "Archivo de solicitudes recolectado"
else
    echo "WARNING: Archivo de solicitudes no encontrado" > "$EVIDENCE_DIR/solicitudes.txt"
fi

# 7. Análisis de métricas
log_with_timestamp "Analizando métricas..."

# Contar operaciones en logs del GC
if [ -f "$EVIDENCE_DIR/gc_logs.txt" ]; then
    # Contar operaciones OK
    operaciones_ok=$(grep -c "Operación.*procesada" "$EVIDENCE_DIR/gc_logs.txt" || echo "0")
    
    # Contar operaciones ERROR
    operaciones_error=$(grep -c "ERROR" "$EVIDENCE_DIR/gc_logs.txt" || echo "0")
    
    # Contar publicaciones por tema
    publicaciones_devolucion=$(grep -c "Topic: devolucion" "$EVIDENCE_DIR/gc_logs.txt" || echo "0")
    publicaciones_renovacion=$(grep -c "Topic: renovacion" "$EVIDENCE_DIR/gc_logs.txt" || echo "0")
    
    echo "operaciones_ok=$operaciones_ok" > "$EVIDENCE_DIR/metricas.txt"
    echo "operaciones_error=$operaciones_error" >> "$EVIDENCE_DIR/metricas.txt"
    echo "publicaciones_devolucion=$publicaciones_devolucion" >> "$EVIDENCE_DIR/metricas.txt"
    echo "publicaciones_renovacion=$publicaciones_renovacion" >> "$EVIDENCE_DIR/metricas.txt"
    
    log_with_timestamp "Métricas analizadas: OK=$operaciones_ok, ERROR=$operaciones_error"
else
    echo "operaciones_ok=0" > "$EVIDENCE_DIR/metricas.txt"
    echo "operaciones_error=0" >> "$EVIDENCE_DIR/metricas.txt"
    echo "publicaciones_devolucion=0" >> "$EVIDENCE_DIR/metricas.txt"
    echo "publicaciones_renovacion=0" >> "$EVIDENCE_DIR/metricas.txt"
    log_with_timestamp "WARNING: No se pudieron analizar métricas (logs no disponibles)"
fi

# 8. Generar resumen
log_with_timestamp "Generando resumen..."

cat > "$EVIDENCE_DIR/resumen.txt" << EOF
=== RESUMEN DE EVIDENCIAS ===
Timestamp: $(date)
Directorio: $EVIDENCE_DIR

=== CONTENEDORES ===
$(cat "$EVIDENCE_DIR/containers_docker_ps.txt")

=== IPs INTERNAS ===
$(cat "$EVIDENCE_DIR/ips.txt" 2>/dev/null || echo "No disponible")

=== MÉTRICAS ===
$(cat "$EVIDENCE_DIR/metricas.txt")

=== ARCHIVOS RECOLECTADOS ===
- containers_docker_ps.txt: Estado de contenedores (docker ps)
- containers_compose_ps.txt: Estado de contenedores (docker compose ps)
- ips.txt: IPs internas de contenedores
- gc_logs.txt: Logs del Gestor de Carga
- actor_dev_logs.txt: Logs del Actor de Devolución
- actor_ren_logs.txt: Logs del Actor de Renovación
- ps_logs.txt: Logs del Proceso Solicitante
- libros_before.json: Estado inicial de libros.json
- libros_after.json: Estado final de libros.json
- libros.diff: Diferencias en libros.json
- solicitudes.txt: Archivo de solicitudes procesadas
- metricas.txt: Métricas del sistema

=== OBSERVACIONES ===
- Recolección completada: $(date)
- Total de archivos: $(find "$EVIDENCE_DIR" -type f | wc -l)
- Tamaño total: $(du -sh "$EVIDENCE_DIR" | cut -f1)
EOF

log_with_timestamp "Resumen generado: $EVIDENCE_DIR/resumen.txt"

# 9. Mostrar resumen final
echo ""
echo "===== RESUMEN DE EVIDENCIAS ====="
echo "Directorio: $EVIDENCE_DIR"
echo "Archivos recolectados: $(find "$EVIDENCE_DIR" -type f | wc -l)"
echo "Tamaño: $(du -sh "$EVIDENCE_DIR" | cut -f1)"
echo ""

# Mostrar métricas principales
if [ -f "$EVIDENCE_DIR/metricas.txt" ]; then
    echo "Métricas principales:"
    cat "$EVIDENCE_DIR/metricas.txt" | while IFS='=' read -r key value; do
        echo "   $key: $value"
    done
fi

echo ""
echo "Recolección de evidencias completada"
echo "Evidencias disponibles en: $EVIDENCE_DIR"

exit 0
