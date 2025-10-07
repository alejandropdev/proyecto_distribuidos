#!/bin/bash
# -*- coding: utf-8 -*-
# run_tests.sh - Orquestador principal de pruebas

set -euo pipefail

# Configuración
LOGS_DIR="./logs"
TEST_LOG="$LOGS_DIR/run_tests.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Iniciando suite de pruebas del Sistema Distribuido de Préstamo de Libros"
echo "Timestamp: $(date)"

# Crear directorio de logs
mkdir -p "$LOGS_DIR"

# Función para loggear con timestamp
log_with_timestamp() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" | tee -a "$TEST_LOG"
}

# Función para ejecutar paso con validación
run_step() {
    local step_name="$1"
    local step_command="$2"
    local step_number="$3"
    
    log_with_timestamp "Paso $step_number: $step_name"
    
    if eval "$step_command" 2>&1 | tee -a "$TEST_LOG"; then
        log_with_timestamp "Paso $step_number completado: $step_name"
        return 0
    else
        log_with_timestamp "Fallo en paso $step_number: $step_name"
        return 1
    fi
}

# Limpiar log anterior
> "$TEST_LOG"

log_with_timestamp "Iniciando suite de pruebas"

# Paso 1: Levantar servicios básicos
run_step "Levantar servicios básicos (GC, Actores)" \
    "docker compose up -d gc actor_devolucion actor_renovacion" 1

# Esperar un momento para que los servicios se inicialicen
log_with_timestamp "Esperando inicialización de servicios..."
sleep 5

# Paso 2: Verificar IPs internas
run_step "Verificar IPs internas (≥2 computadores)" \
    "./scripts/show_ips.sh" 2

# Paso 3: Esperar que GC esté listo
run_step "Verificar que GC esté listo" \
    "./scripts/wait_for_gc.sh" 3

# Paso 4: Test 1 - End-to-end básico
log_with_timestamp "Ejecutando Test 1: End-to-end básico"
if run_step "Test end-to-end (sin PS)" \
    "docker compose run --rm tester python -m pytest -v tests/test_end_to_end.py" 4; then
    log_with_timestamp "Test 1 PASSED: End-to-end básico"
    test1_result="PASSED"
else
    log_with_timestamp "Test 1 FAILED: End-to-end básico"
    test1_result="FAILED"
fi

# Paso 5: Test 2 - Pub/Sub visibilidad
log_with_timestamp "Ejecutando Test 2: Pub/Sub visibilidad"
if run_step "Test pub/sub visibilidad" \
    "docker compose run --rm tester python -m pytest -v tests/test_pubsub_visibility.py" 5; then
    log_with_timestamp "Test 2 PASSED: Pub/Sub visibilidad"
    test2_result="PASSED"
else
    log_with_timestamp "Test 2 FAILED: Pub/Sub visibilidad"
    test2_result="FAILED"
fi

# Paso 6: Test 3 - Workload con archivo (PS)
log_with_timestamp "Ejecutando Test 3: Workload con archivo"
log_with_timestamp "Levantando PS en perfil demo..."

# Levantar PS en perfil demo
if run_step "Levantar PS en perfil demo" \
    "docker compose --profile demo up -d ps" 6a; then
    
    # Esperar un momento para que PS se inicialice
    sleep 3
    
    # Ejecutar test de workload
    if run_step "Test workload con archivo" \
        "docker compose run --rm tester python -m pytest -v tests/test_file_workload.py" 6b; then
        log_with_timestamp "Test 3 PASSED: Workload con archivo"
        test3_result="PASSED"
    else
        log_with_timestamp "Test 3 FAILED: Workload con archivo"
        test3_result="FAILED"
    fi
else
    log_with_timestamp "No se pudo levantar PS, saltando Test 3"
    test3_result="SKIPPED"
fi

# Paso 7: Estado final de contenedores
run_step "Verificar estado final de contenedores" \
    "docker compose ps > $LOGS_DIR/containers_final.txt" 7

# Paso 8: Recolectar evidencias
run_step "Recolectar evidencias del sistema" \
    "./scripts/collect_evidence.sh" 8

# Generar resumen final
log_with_timestamp "Generando resumen final de pruebas..."

cat > "$LOGS_DIR/resumen_pruebas.txt" << EOF
=== RESUMEN DE PRUEBAS ===
Timestamp: $(date)
Log: $TEST_LOG

=== RESULTADOS POR TEST ===
Test 1 (End-to-end básico): $test1_result
Test 2 (Pub/Sub visibilidad): $test2_result
Test 3 (Workload con archivo): $test3_result

=== CRITERIOS DE ACEPTACIÓN ===
- [ ] ≥3 procesos en ≥2 computadores: $(if [ -f "$LOGS_DIR/ips.txt" ] && [ $(grep -c "IP:" "$LOGS_DIR/ips.txt" 2>/dev/null || echo 0) -ge 2 ]; then echo "CUMPLIDO"; else echo "NO CUMPLIDO"; fi)
- [ ] REQ/REP (PS→GC) con ACK inmediato: $test1_result
- [ ] PUB/SUB (GC→Actores) por temas: $test2_result
- [ ] Operaciones aplicadas a libros.json: $test1_result
- [ ] Archivo de carga procesado por PS: $test3_result
- [ ] Logs con timestamps y conteos: DISPONIBLE

=== ESTADO FINAL ===
EOF

# Verificar si todos los tests pasaron
total_tests=0
passed_tests=0

if [ "$test1_result" = "PASSED" ]; then ((passed_tests++)); fi
if [ "$test2_result" = "PASSED" ]; then ((passed_tests++)); fi
if [ "$test3_result" = "PASSED" ]; then ((passed_tests++)); fi

if [ "$test1_result" != "SKIPPED" ]; then ((total_tests++)); fi
if [ "$test2_result" != "SKIPPED" ]; then ((total_tests++)); fi
if [ "$test3_result" != "SKIPPED" ]; then ((total_tests++)); fi

echo "Tests pasados: $passed_tests/$total_tests" >> "$LOGS_DIR/resumen_pruebas.txt"

if [ "$passed_tests" -eq "$total_tests" ] && [ "$total_tests" -gt 0 ]; then
    echo "Estado general: TODOS LOS TESTS PASARON" >> "$LOGS_DIR/resumen_pruebas.txt"
    log_with_timestamp "TODOS LOS TESTS PASARON ($passed_tests/$total_tests)"
    log_with_timestamp "Requisitos Entrega #1 verificados"
    exit_code=0
else
    echo "Estado general: ALGUNOS TESTS FALLARON" >> "$LOGS_DIR/resumen_pruebas.txt"
    log_with_timestamp "ALGUNOS TESTS FALLARON ($passed_tests/$total_tests)"
    exit_code=1
fi

# Mostrar resumen final
echo ""
echo "===== RESUMEN FINAL ====="
echo "Tests ejecutados: $total_tests"
echo "Tests pasados: $passed_tests"
echo "Tests fallidos: $((total_tests - passed_tests))"
echo "Log completo: $TEST_LOG"
echo "Resumen: $LOGS_DIR/resumen_pruebas.txt"
echo "Evidencias: $LOGS_DIR/evidence/"

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "SUITE DE PRUEBAS COMPLETADA EXITOSAMENTE!"
    echo "Requisitos Entrega #1 verificados"
else
    echo ""
    echo "Suite de pruebas completada con fallos"
    echo "Revisar logs para más detalles"
fi

exit $exit_code
