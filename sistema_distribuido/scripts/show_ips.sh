#!/bin/bash
# -*- coding: utf-8 -*-
# show_ips.sh - Muestra IPs internas de los contenedores

set -euo pipefail

# Configuración
LOGS_DIR="./logs"
IPS_FILE="$LOGS_DIR/ips.txt"

echo "Obteniendo IPs internas de los contenedores..."

# Crear directorio de logs si no existe
mkdir -p "$LOGS_DIR"

# Limpiar archivo de IPs
> "$IPS_FILE"

# Servicios a verificar
SERVICES=("gc" "actor_dev" "actor_ren" "ps" "tester")

# Función para obtener IP de un contenedor
get_container_ip() {
    local container_name=$1
    local ip
    
    echo "Obteniendo IP para $container_name..."
    
    # Verificar si el contenedor existe y está corriendo
    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "WARNING: Contenedor $container_name no está corriendo"
        return 1
    fi
    
    # Obtener IP del contenedor
    ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_name" 2>/dev/null || echo "")
    
    if [ -z "$ip" ] || [ "$ip" = "<no value>" ]; then
        echo "ERROR: No se pudo obtener IP para $container_name"
        return 1
    fi
    
    echo "$container_name IP: $ip"
    echo "$container_name IP: $ip" >> "$IPS_FILE"
    return 0
}

# Obtener IPs de todos los servicios
ips_obtenidas=0
ips_unicas=()

for service in "${SERVICES[@]}"; do
    if get_container_ip "$service"; then
        ((ips_obtenidas++))
        ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$service" 2>/dev/null)
        if [ -n "$ip" ] && [ "$ip" != "<no value>" ]; then
            ips_unicas+=("$ip")
        fi
    fi
done

echo ""
echo "Resumen de IPs obtenidas:"
echo "================================"

# Mostrar IPs únicas
if [ ${#ips_unicas[@]} -gt 0 ]; then
    printf '%s\n' "${ips_unicas[@]}" | sort -u | while read -r ip; do
        echo "IP única: $ip"
    done
    
    # Contar IPs únicas
    ips_unicas_count=$(printf '%s\n' "${ips_unicas[@]}" | sort -u | wc -l)
    echo ""
    echo "Total de IPs únicas: $ips_unicas_count"
    echo "Total de contenedores con IP: $ips_obtenidas"
    
    # Validar criterio de "≥2 computadores"
    if [ "$ips_unicas_count" -ge 2 ]; then
        echo "Criterio cumplido: ≥2 computadores (IPs distintas)"
    else
        echo "Criterio NO cumplido: Se requieren ≥2 IPs distintas"
        echo "IPs encontradas: ${ips_unicas[*]}"
        exit 1
    fi
else
    echo "No se obtuvieron IPs válidas"
    exit 1
fi

echo ""
echo "IPs guardadas en: $IPS_FILE"
echo "Verificación de IPs completada"

exit 0
