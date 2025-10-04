# -*- coding: utf-8 -*-
# Makefile - Sistema Distribuido de Préstamo de Libros
# Suite de verificación minuciosa para validar cumplimiento de Entrega #1

.PHONY: help up down test demo evidence logs clean status ips wait-gc

# Configuración
DOCKER_COMPOSE = docker compose
LOGS_DIR = logs
SCRIPTS_DIR = scripts

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Ayuda por defecto
help: ## Mostrar ayuda
	@echo "$(GREEN)Sistema Distribuido de Préstamo de Libros$(NC)"
	@echo "$(GREEN)============================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Ejemplos:$(NC)"
	@echo "  make up          # Levantar servicios básicos"
	@echo "  make test        # Ejecutar suite completa de pruebas"
	@echo "  make demo        # Levantar con PS para demostración"
	@echo "  make evidence    # Recolectar evidencias del sistema"

# Objetivos principales
up: ## Levantar servicios básicos (GC + Actores)
	@echo "$(GREEN)🚀 Levantando servicios básicos...$(NC)"
	@$(DOCKER_COMPOSE) up -d gc actor_devolucion actor_renovacion
	@echo "$(GREEN)✅ Servicios básicos levantados$(NC)"
	@echo "$(YELLOW)📋 Estado:$(NC)"
	@$(DOCKER_COMPOSE) ps

down: ## Detener todos los servicios
	@echo "$(YELLOW)🛑 Deteniendo todos los servicios...$(NC)"
	@$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

test: ## Ejecutar suite completa de pruebas
	@echo "$(GREEN)🧪 Ejecutando suite completa de pruebas...$(NC)"
	@echo "$(YELLOW)📊 Esto incluye:$(NC)"
	@echo "   - Levantar servicios básicos"
	@echo "   - Verificar IPs internas (≥2 computadores)"
	@echo "   - Test end-to-end (REQ/REP + PUB/SUB)"
	@echo "   - Test pub/sub visibilidad"
	@echo "   - Test workload con archivo"
	@echo "   - Recolección de evidencias"
	@echo ""
	@$(SCRIPTS_DIR)/run_tests.sh
	@echo ""
	@echo "$(GREEN)📊 Resultados disponibles en: $(LOGS_DIR)/$(NC)"

demo: ## Levantar con PS para demostración
	@echo "$(GREEN)🎭 Levantando sistema completo para demostración...$(NC)"
	@$(DOCKER_COMPOSE) --profile demo up -d
	@echo "$(GREEN)✅ Sistema completo levantado$(NC)"
	@echo "$(YELLOW)📋 Estado:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(YELLOW)📝 Para ver logs en tiempo real:$(NC)"
	@echo "  make logs"

evidence: ## Recolectar evidencias del sistema
	@echo "$(GREEN)📊 Recolectando evidencias del sistema...$(NC)"
	@$(SCRIPTS_DIR)/collect_evidence.sh
	@echo "$(GREEN)✅ Evidencias recolectadas en: $(LOGS_DIR)/evidence/$(NC)"

logs: ## Mostrar logs de todos los servicios
	@echo "$(GREEN)📝 Mostrando logs de todos los servicios...$(NC)"
	@$(DOCKER_COMPOSE) logs --tail=200 gc actor_devolucion actor_renovacion ps || true
	@echo "$(GREEN)✅ Logs mostrados$(NC)"

# Objetivos de diagnóstico
status: ## Mostrar estado de contenedores
	@echo "$(GREEN)📋 Estado de contenedores:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(GREEN)🐳 Contenedores Docker:$(NC)"
	@docker ps --filter "name=gc\|actor_\|ps\|tester" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

ips: ## Mostrar IPs internas de contenedores
	@echo "$(GREEN)🌐 Obteniendo IPs internas...$(NC)"
	@$(SCRIPTS_DIR)/show_ips.sh

wait-gc: ## Esperar hasta que GC esté listo
	@echo "$(GREEN)⏳ Esperando que GC esté listo...$(NC)"
	@$(SCRIPTS_DIR)/wait_for_gc.sh

# Objetivos de desarrollo
build: ## Construir imágenes Docker
	@echo "$(GREEN)🔨 Construyendo imágenes Docker...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imágenes construidas$(NC)"

rebuild: ## Reconstruir imágenes Docker
	@echo "$(GREEN)🔄 Reconstruyendo imágenes Docker...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)✅ Imágenes reconstruidas$(NC)"

# Objetivos de pruebas específicas
test-e2e: ## Ejecutar solo test end-to-end
	@echo "$(GREEN)🧪 Ejecutando test end-to-end...$(NC)"
	@$(DOCKER_COMPOSE) run --rm tester python -m pytest -v tests/test_end_to_end.py

test-pubsub: ## Ejecutar solo test pub/sub
	@echo "$(GREEN)🧪 Ejecutando test pub/sub...$(NC)"
	@$(DOCKER_COMPOSE) run --rm tester python -m pytest -v tests/test_pubsub_visibility.py

test-workload: ## Ejecutar solo test workload
	@echo "$(GREEN)🧪 Ejecutando test workload...$(NC)"
	@$(DOCKER_COMPOSE) --profile demo up -d ps
	@$(DOCKER_COMPOSE) run --rm tester python -m pytest -v tests/test_file_workload.py

# Objetivos de limpieza
clean: ## Limpiar contenedores, volúmenes y logs
	@echo "$(YELLOW)🧹 Limpiando sistema...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@rm -rf $(LOGS_DIR)/*
	@echo "$(GREEN)✅ Sistema limpiado$(NC)"

clean-logs: ## Limpiar solo logs
	@echo "$(YELLOW)🧹 Limpiando logs...$(NC)"
	@rm -rf $(LOGS_DIR)/*
	@echo "$(GREEN)✅ Logs limpiados$(NC)"

clean-containers: ## Limpiar solo contenedores
	@echo "$(YELLOW)🧹 Limpiando contenedores...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✅ Contenedores limpiados$(NC)"

# Objetivos de información
info: ## Mostrar información del sistema
	@echo "$(GREEN)ℹ️  Información del Sistema$(NC)"
	@echo "$(GREEN)========================$(NC)"
	@echo ""
	@echo "$(YELLOW)🐳 Docker:$(NC)"
	@docker --version
	@echo ""
	@echo "$(YELLOW)🐙 Docker Compose:$(NC)"
	@$(DOCKER_COMPOSE) version
	@echo ""
	@echo "$(YELLOW)📁 Estructura:$(NC)"
	@echo "  - Servicios: 4 (GC + 2 Actores + PS)"
	@echo "  - Tests: 3 (end-to-end, pub/sub, workload)"
	@echo "  - Scripts: 4 (orquestación y diagnóstico)"
	@echo "  - Documentación: 5 archivos"
	@echo ""
	@echo "$(YELLOW)🔌 Puertos:$(NC)"
	@echo "  - GC REQ/REP: 5001"
	@echo "  - GC PUB/SUB: 5002"
	@echo ""
	@echo "$(YELLOW)📊 Requisitos Entrega #1:$(NC)"
	@echo "  - ≥3 procesos: ✅ (4 procesos)"
	@echo "  - ≥2 computadores: ✅ (IPs distintas)"
	@echo "  - REQ/REP: ✅ (PS ↔ GC)"
	@echo "  - PUB/SUB: ✅ (GC → Actores)"
	@echo "  - Operaciones: ✅ (RENOVACIÓN + DEVOLUCIÓN)"
	@echo "  - Archivo de carga: ✅ (PS procesa solicitudes.txt)"

# Objetivos de validación
validate: ## Validar configuración del sistema
	@echo "$(GREEN)🔍 Validando configuración del sistema...$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Verificando archivos requeridos:$(NC)"
	@test -f docker-compose.yml || (echo "$(RED)❌ docker-compose.yml no encontrado$(NC)" && exit 1)
	@test -f requirements.txt || (echo "$(RED)❌ requirements.txt no encontrado$(NC)" && exit 1)
	@test -d tests/ || (echo "$(RED)❌ Directorio tests/ no encontrado$(NC)" && exit 1)
	@test -d scripts/ || (echo "$(RED)❌ Directorio scripts/ no encontrado$(NC)" && exit 1)
	@test -d data/ || (echo "$(RED)❌ Directorio data/ no encontrado$(NC)" && exit 1)
	@echo "$(GREEN)✅ Archivos requeridos encontrados$(NC)"
	@echo ""
	@echo "$(YELLOW)🔧 Verificando scripts ejecutables:$(NC)"
	@test -x scripts/run_tests.sh || (echo "$(RED)❌ scripts/run_tests.sh no es ejecutable$(NC)" && exit 1)
	@test -x scripts/collect_evidence.sh || (echo "$(RED)❌ scripts/collect_evidence.sh no es ejecutable$(NC)" && exit 1)
	@test -x scripts/show_ips.sh || (echo "$(RED)❌ scripts/show_ips.sh no es ejecutable$(NC)" && exit 1)
	@test -x scripts/wait_for_gc.sh || (echo "$(RED)❌ scripts/wait_for_gc.sh no es ejecutable$(NC)" && exit 1)
	@echo "$(GREEN)✅ Scripts ejecutables$(NC)"
	@echo ""
	@echo "$(YELLOW)📊 Verificando datos de prueba:$(NC)"
	@test -f data/libros.json || (echo "$(RED)❌ data/libros.json no encontrado$(NC)" && exit 1)
	@test -f data/solicitudes.txt || (echo "$(RED)❌ data/solicitudes.txt no encontrado$(NC)" && exit 1)
	@echo "$(GREEN)✅ Datos de prueba encontrados$(NC)"
	@echo ""
	@echo "$(GREEN)✅ Configuración del sistema válida$(NC)"

# Objetivo por defecto
.DEFAULT_GOAL := help
