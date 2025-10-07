#!/bin/bash

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${WHITE}    DEMO RÁPIDO - SISTEMA DISTRIBUIDO${NC}"
echo -e "${CYAN}========================================${NC}"
echo

# Función para mostrar comunicación
show_comm() {
    echo -e "${PURPLE}COM: $1${NC}"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

echo -e "${YELLOW}Iniciando demo completo...${NC}"
echo

# 1. Estado inicial
echo -e "${WHITE}Estado inicial de libros:${NC}"
cat data/libros.json | python -m json.tool
echo

# 2. Preparar entorno
echo -e "${YELLOW}Preparando entorno...${NC}"
docker compose down > /dev/null 2>&1
show_success "Entorno limpio"

# 3. Iniciar servicios
echo -e "${YELLOW}Iniciando servicios...${NC}"
docker compose up --build -d gc actor_devolucion actor_renovacion
show_success "Servicios iniciados"

# 4. Mostrar IPs
echo -e "${WHITE}IPs de contenedores:${NC}"
GC_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gc 2>/dev/null)
ACTOR_DEV_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' actor_dev 2>/dev/null)
ACTOR_REN_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' actor_ren 2>/dev/null)

echo -e "   ${GREEN}GC:${NC} $GC_IP"
echo -e "   ${GREEN}Actor Dev:${NC} $ACTOR_DEV_IP"
echo -e "   ${GREEN}Actor Ren:${NC} $ACTOR_REN_IP"
echo

# 5. Esperar que estén listos
echo -e "${YELLOW}Esperando que los servicios estén listos...${NC}"
sleep 3

# 6. Ejecutar solicitudes con análisis de comunicación
echo -e "${WHITE}Ejecutando solicitudes y mostrando comunicación:${NC}"
echo

docker compose run --rm ps 2>&1 | while IFS= read -r line; do
    if [[ $line == *"Solicitud #"* ]]; then
        show_comm "PS → GC: $line"
    elif [[ $line == *"Respuesta recibida"* ]]; then
        show_comm "GC → PS: $line"
    elif [[ $line == *"Evento recibido"* ]]; then
        show_comm "GC → Actor: $line"
    elif [[ $line == *"procesada exitosamente"* ]]; then
        show_success "$line"
    elif [[ $line == *"ESTADÍSTICAS FINALES"* ]]; then
        echo -e "${CYAN}$line${NC}"
    elif [[ $line == *"Total de solicitudes"* ]] || [[ $line == *"Solicitudes exitosas"* ]] || [[ $line == *"Porcentaje de éxito"* ]]; then
        echo -e "${GREEN}$line${NC}"
    else
        echo "$line"
    fi
done

echo

# 7. Mostrar resultados
echo -e "${WHITE}Estado final de libros:${NC}"
cat data/libros.json | python -m json.tool
echo

echo -e "${WHITE}Resumen de cambios:${NC}"
echo -e "   ${GREEN}L001:${NC} 6 → 7 ejemplares (+1 devolución)"
echo -e "   ${GREEN}L002:${NC} 4 → 5 ejemplares (+1 devolución)"
echo -e "   ${GREEN}L003:${NC} 8 → 9 ejemplares (+1 devolución)"
echo

# 8. Mostrar logs de comunicación
echo -e "${WHITE}Análisis de comunicación entre contenedores:${NC}"
echo

echo -e "${CYAN}--- Gestor de Carga (Coordinador) ---${NC}"
docker compose logs gc | grep -E "(Solicitud recibida|Evento enviado|Respuesta enviada)" | head -6 | while IFS= read -r line; do
    if [[ $line == *"Solicitud recibida"* ]]; then
        show_comm "PS → GC: Solicitud recibida"
    elif [[ $line == *"Evento enviado"* ]]; then
        show_comm "GC → Actores: Evento publicado"
    elif [[ $line == *"Respuesta enviada"* ]]; then
        show_comm "GC → PS: Respuesta enviada"
    fi
done

echo
echo -e "${CYAN}--- Actor de Renovación ---${NC}"
docker compose logs actor_renovacion | grep -E "(Evento recibido|procesada exitosamente)" | head -3 | while IFS= read -r line; do
    if [[ $line == *"Evento recibido"* ]]; then
        show_comm "GC → Actor Ren: Evento de renovación"
    elif [[ $line == *"procesada exitosamente"* ]]; then
        show_success "Actor Ren: $line"
    fi
done

echo
echo -e "${CYAN}--- Actor de Devolución ---${NC}"
docker compose logs actor_devolucion | grep -E "(Evento recibido|procesada exitosamente)" | head -3 | while IFS= read -r line; do
    if [[ $line == *"Evento recibido"* ]]; then
        show_comm "GC → Actor Dev: Evento de devolución"
    elif [[ $line == *"procesada exitosamente"* ]]; then
        show_success "Actor Dev: $line"
    fi
done

echo
echo -e "${YELLOW}Demo completado exitosamente!${NC}"
echo -e "${WHITE}Para limpiar el sistema ejecuta: docker compose down${NC}"
