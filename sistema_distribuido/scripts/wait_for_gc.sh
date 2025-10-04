#!/bin/bash
# -*- coding: utf-8 -*-
# wait_for_gc.sh - Espera hasta que el Gestor de Carga esté listo

set -euo pipefail

# Configuración
MAX_ATTEMPTS=30
SLEEP_INTERVAL=1

echo "🔄 Esperando que el Gestor de Carga esté listo..."
echo "📍 Endpoint: tcp://gc:5001"
echo "⏱️  Máximo $MAX_ATTEMPTS intentos con intervalo de ${SLEEP_INTERVAL}s"

# Función para probar conexión al GC usando docker compose
test_gc_connection() {
    local attempt=$1
    
    echo "🔍 Intento $attempt/$MAX_ATTEMPTS: Probando conexión al GC..."
    
    # Usar docker compose run para probar la conexión desde dentro de la red
    if docker compose run --rm tester python -c "
import zmq
import json
import sys

try:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 3000)  # 3 segundos timeout
    socket.setsockopt(zmq.SNDTIMEO, 3000)  # 3 segundos timeout para envío
    socket.connect('tcp://gc:5001')
    
    # Enviar solicitud de prueba (operación inválida)
    test_payload = {
        'op': 'TEST_CONNECTION',
        'libro_id': 'TEST',
        'usuario_id': 'TEST'
    }
    
    socket.send(json.dumps(test_payload).encode('utf-8'))
    response_bytes = socket.recv()
    response = json.loads(response_bytes.decode('utf-8'))
    
    socket.close()
    context.term()
    
    # Cualquier respuesta (OK o ERROR) indica que GC está listo
    print(f'✅ GC responde: {response}')
    sys.exit(0)
    
except zmq.Again:
    print('❌ Timeout conectando al GC')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error conectando al GC: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ GC está listo y respondiendo"
        return 0
    else
        echo "❌ GC no responde en intento $attempt"
        return 1
    fi
}

# Loop principal de espera
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    if test_gc_connection $attempt; then
        echo "🎉 Gestor de Carga está listo después de $attempt intentos"
        exit 0
    fi
    
    if [ $attempt -lt $MAX_ATTEMPTS ]; then
        echo "⏳ Esperando ${SLEEP_INTERVAL}s antes del siguiente intento..."
        sleep $SLEEP_INTERVAL
    fi
done

echo "❌ GC NO LISTO después de $MAX_ATTEMPTS intentos"
echo "🔍 Verificando estado de contenedores..."
docker ps --filter "name=gc" || true
echo "📋 Logs del GC:"
docker logs gc --tail=20 || true

exit 1
