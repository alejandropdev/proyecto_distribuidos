#!/bin/bash

# Script de Demostración para Profesor
# Sistema Distribuido de Préstamo de Libros

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Sistema Distribuido de Biblioteca${NC}"
echo -e "${BLUE}Menú de Opciones${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Ejecute este script desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Verificar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"
if ! python -c "import zmq, rich, typer" 2>/dev/null; then
    echo -e "${RED}Instalando dependencias...${NC}"
    pip install -r requirements.txt
fi

echo -e "${GREEN}✓ Dependencias verificadas${NC}"
echo ""

# Iniciar sistema
echo -e "${YELLOW}Iniciando sistema interactivo...${NC}"
echo -e "${BLUE}Presione Ctrl+C para salir en cualquier momento${NC}"
echo ""

python demo_profesor.py
