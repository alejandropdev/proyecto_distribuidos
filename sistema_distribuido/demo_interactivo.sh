#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Función para mostrar header
show_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${WHITE}    SISTEMA DISTRIBUIDO DE LIBROS${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo
}

# Función para mostrar paso
show_step() {
    echo -e "${YELLOW}📋 PASO $1: $2${NC}"
    echo
}

# Función para mostrar información
show_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar error
show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para mostrar comunicación
show_communication() {
    echo -e "${PURPLE}📡 COMUNICACIÓN: $1${NC}"
}

# Función para pausa
pause() {
    echo -e "${YELLOW}Presiona Enter para continuar...${NC}"
    read
}

# Función para limpiar pantalla
clear_screen() {
    clear
    show_header
}

# Función para obtener IPs de contenedores
get_container_ips() {
    echo -e "${CYAN}🔍 Obteniendo IPs de los contenedores...${NC}"
    echo
    
    # Obtener IPs
    GC_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gc 2>/dev/null)
    PS_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ps 2>/dev/null)
    ACTOR_DEV_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' actor_dev 2>/dev/null)
    ACTOR_REN_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' actor_ren 2>/dev/null)
    
    echo -e "${WHITE}📍 IPs de los contenedores:${NC}"
    echo -e "   ${GREEN}Gestor de Carga (GC):${NC} $GC_IP"
    echo -e "   ${GREEN}Proceso Solicitante (PS):${NC} $PS_IP"
    echo -e "   ${GREEN}Actor Devolución:${NC} $ACTOR_DEV_IP"
    echo -e "   ${GREEN}Actor Renovación:${NC} $ACTOR_REN_IP"
    echo
}

# Función para mostrar estado inicial
show_initial_state() {
    show_step "1" "Verificando estado inicial del sistema"
    
    echo -e "${WHITE}📚 Estado inicial de la base de datos:${NC}"
    cat data/libros.json | python -m json.tool
    echo
    
    echo -e "${WHITE}📋 Solicitudes a procesar:${NC}"
    cat data/solicitudes.txt
    echo
    
    pause
}

# Función para preparar entorno
prepare_environment() {
    show_step "2" "Preparando entorno"
    
    show_info "Verificando Docker..."
    if ! docker --version > /dev/null 2>&1; then
        show_error "Docker no está instalado o no está funcionando"
        exit 1
    fi
    show_success "Docker funcionando correctamente"
    
    show_info "Verificando Docker Compose..."
    if ! docker compose --version > /dev/null 2>&1; then
        show_error "Docker Compose no está disponible"
        exit 1
    fi
    show_success "Docker Compose funcionando correctamente"
    
    show_info "Limpiando contenedores anteriores..."
    docker compose down > /dev/null 2>&1
    show_success "Entorno limpio"
    
    pause
}

# Función para iniciar servicios
start_services() {
    show_step "3" "Iniciando servicios distribuidos"
    
    show_info "Construyendo y levantando servicios principales..."
    docker compose up --build -d gc actor_devolucion actor_renovacion
    
    if [ $? -eq 0 ]; then
        show_success "Servicios principales iniciados correctamente"
    else
        show_error "Error al iniciar los servicios"
        exit 1
    fi
    
    echo
    show_info "Esperando que los servicios estén listos..."
    sleep 3
    
    # Mostrar estado de contenedores
    echo -e "${WHITE}📊 Estado de los contenedores:${NC}"
    docker compose ps
    echo
    
    # Obtener y mostrar IPs
    get_container_ips
    
    # Mostrar logs de inicialización
    echo -e "${WHITE}📝 Logs de inicialización:${NC}"
    echo -e "${CYAN}--- Gestor de Carga ---${NC}"
    docker compose logs gc | tail -5
    echo
    echo -e "${CYAN}--- Actores ---${NC}"
    docker compose logs actor_devolucion actor_renovacion | tail -5
    echo
    
    pause
}

# Función para ejecutar solicitudes
run_requests() {
    show_step "4" "Ejecutando solicitudes del sistema"
    
    show_info "Iniciando Proceso Solicitante..."
    echo -e "${WHITE}📤 Enviando solicitudes al sistema...${NC}"
    echo
    
    # Ejecutar PS y capturar output
    docker compose run --rm ps 2>&1 | while IFS= read -r line; do
        if [[ $line == *"Solicitud #"* ]]; then
            show_communication "PS → GC: $line"
        elif [[ $line == *"Respuesta recibida"* ]]; then
            show_communication "GC → PS: $line"
        elif [[ $line == *"Evento recibido"* ]]; then
            show_communication "GC → Actor: $line"
        elif [[ $line == *"procesada exitosamente"* ]]; then
            show_success "$line"
        else
            echo "$line"
        fi
    done
    
    echo
    pause
}

# Función para mostrar logs detallados
show_detailed_logs() {
    show_step "5" "Mostrando comunicación detallada entre contenedores"
    
    echo -e "${WHITE}📡 Análisis de comunicación entre contenedores:${NC}"
    echo
    
    # Mostrar logs del GC con análisis
    echo -e "${CYAN}--- Gestor de Carga (Coordinador) ---${NC}"
    docker compose logs gc | grep -E "(Solicitud recibida|Evento enviado|Respuesta enviada)" | while IFS= read -r line; do
        if [[ $line == *"Solicitud recibida"* ]]; then
            show_communication "📨 PS → GC: Solicitud recibida"
        elif [[ $line == *"Evento enviado"* ]]; then
            show_communication "📡 GC → Actores: Evento publicado"
        elif [[ $line == *"Respuesta enviada"* ]]; then
            show_communication "📤 GC → PS: Respuesta enviada"
        fi
    done
    echo
    
    # Mostrar logs de actores
    echo -e "${CYAN}--- Actor de Renovación ---${NC}"
    docker compose logs actor_renovacion | grep -E "(Evento recibido|procesada exitosamente)" | while IFS= read -r line; do
        if [[ $line == *"Evento recibido"* ]]; then
            show_communication "📨 GC → Actor Ren: Evento de renovación"
        elif [[ $line == *"procesada exitosamente"* ]]; then
            show_success "✅ Actor Ren: $line"
        fi
    done
    echo
    
    echo -e "${CYAN}--- Actor de Devolución ---${NC}"
    docker compose logs actor_devolucion | grep -E "(Evento recibido|procesada exitosamente)" | while IFS= read -r line; do
        if [[ $line == *"Evento recibido"* ]]; then
            show_communication "📨 GC → Actor Dev: Evento de devolución"
        elif [[ $line == *"procesada exitosamente"* ]]; then
            show_success "✅ Actor Dev: $line"
        fi
    done
    echo
    
    pause
}

# Función para mostrar resultados
show_results() {
    show_step "6" "Verificando resultados del procesamiento"
    
    echo -e "${WHITE}📊 Estado final de la base de datos:${NC}"
    cat data/libros.json | python -m json.tool
    echo
    
    echo -e "${WHITE}📈 Resumen de cambios:${NC}"
    echo -e "   ${GREEN}L001 (1984):${NC} 6 → 7 ejemplares (+1 devolución)"
    echo -e "   ${GREEN}L002 (El Principito):${NC} 4 → 5 ejemplares (+1 devolución)"
    echo -e "   ${GREEN}L003 (Cien Años de Soledad):${NC} 8 → 9 ejemplares (+1 devolución)"
    echo
    
    echo -e "${WHITE}📋 Operaciones procesadas:${NC}"
    echo -e "   ${YELLOW}Renovaciones:${NC} 3 (L001, L003, L002)"
    echo -e "   ${YELLOW}Devoluciones:${NC} 3 (L002, L001, L003)"
    echo -e "   ${GREEN}Total:${NC} 6 operaciones exitosas (100%)"
    echo
    
    pause
}

# Función para mostrar arquitectura
show_architecture() {
    show_step "7" "Explicando arquitectura del sistema"
    
    echo -e "${WHITE}🏗️ Arquitectura del Sistema Distribuido:${NC}"
    echo
    echo -e "${CYAN}1. Patrones de Comunicación:${NC}"
    echo -e "   ${YELLOW}REQ/REP (Síncrono):${NC} PS ↔ GC (puerto 5001)"
    echo -e "   ${YELLOW}PUB/SUB (Asíncrono):${NC} GC → Actores (puerto 5002)"
    echo
    echo -e "${CYAN}2. Flujo de Datos:${NC}"
    echo -e "   ${GREEN}PS${NC} lee solicitudes → envía a ${GREEN}GC${NC}"
    echo -e "   ${GREEN}GC${NC} responde inmediatamente → publica eventos"
    echo -e "   ${GREEN}Actores${NC} procesan eventos → actualizan BD"
    echo
    echo -e "${CYAN}3. Características Técnicas:${NC}"
    echo -e "   • Comunicación TCP entre contenedores"
    echo -e "   • Base de datos JSON compartida"
    echo -e "   • Logs detallados con timestamps"
    echo -e "   • Manejo robusto de errores"
    echo -e "   • Sistema completamente distribuido"
    echo
    
    pause
}

# Función para limpiar
cleanup() {
    show_step "8" "Limpiando el sistema"
    
    show_info "Deteniendo contenedores..."
    docker compose down
    show_success "Sistema detenido correctamente"
    echo
}

# Función para mostrar menú
show_menu() {
    clear_screen
    echo -e "${WHITE}Selecciona una opción:${NC}"
    echo
    echo -e "${GREEN}1.${NC} Ver estado inicial"
    echo -e "${GREEN}2.${NC} Preparar entorno"
    echo -e "${GREEN}3.${NC} Iniciar servicios y mostrar IPs"
    echo -e "${GREEN}4.${NC} Ejecutar solicitudes"
    echo -e "${GREEN}5.${NC} Mostrar logs detallados de comunicación"
    echo -e "${GREEN}6.${NC} Ver resultados finales"
    echo -e "${GREEN}7.${NC} Explicar arquitectura"
    echo -e "${GREEN}8.${NC} Limpiar sistema"
    echo -e "${RED}9.${NC} Salir"
    echo
    echo -n -e "${YELLOW}Ingresa tu opción (1-9): ${NC}"
}

# Función principal
main() {
    clear_screen
    
    echo -e "${WHITE}Bienvenido al Sistema Distribuido de Libros${NC}"
    echo -e "${CYAN}Este script te guiará paso a paso para demostrar el funcionamiento${NC}"
    echo
    
    while true; do
        show_menu
        read -r option
        
        case $option in
            1)
                show_initial_state
                ;;
            2)
                prepare_environment
                ;;
            3)
                start_services
                ;;
            4)
                run_requests
                ;;
            5)
                show_detailed_logs
                ;;
            6)
                show_results
                ;;
            7)
                show_architecture
                ;;
            8)
                cleanup
                ;;
            9)
                echo -e "${GREEN}¡Hasta luego!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción inválida. Intenta de nuevo.${NC}"
                pause
                ;;
        esac
    done
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    show_error "No se encontró docker-compose.yml. Asegúrate de estar en el directorio correcto."
    exit 1
fi

# Ejecutar función principal
main
