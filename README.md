# Sistema Distribuido de Préstamo de Libros

## 📋 Contexto del Proyecto

Este proyecto implementa un sistema distribuido de préstamo de libros para la Universidad Ada Lovelace, desarrollado como parte de un curso de sistemas distribuidos. El sistema está diseñado para funcionar en múltiples máquinas con comunicación distribuida usando ZeroMQ.

## 🏗️ Arquitectura del Sistema

### Componentes Principales
- **PS (Proceso Solicitante)**: Cliente que envía solicitudes (renovar, devolver, prestar)
- **GC (Gestor Central)**: Recibe solicitudes de PS y las enruta a los actores correctos
- **AR (Actor Renovación)**: Procesa renovaciones via PUB/SUB
- **AD (Actor Devolución)**: Procesa devoluciones via PUB/SUB  
- **AP (Actor Préstamo)**: Procesa préstamos via REQ/REP
- **GA (Gestor de Almacenamiento)**: Servidor de almacenamiento con replicación

### Patrones de Comunicación
- **PS ↔ GC**: REQ/REP (síncrono)
- **GC → AR/AD**: PUB/SUB (asíncrono)
- **GC ↔ AP**: REQ/REP (síncrono)
- **Actores ↔ GA**: REQ/REP (síncrono)
- **GA_A ↔ GA_B**: Replicación (asíncrono)

### Operaciones Implementadas
- **RENOVAR**: Renovación de préstamo (1 semana adicional, máximo 2 renovaciones)
- **DEVOLVER**: Devolución de libro (marca como disponible)
- **PRESTAR**: Préstamo de libro (verificación de disponibilidad)

## 🚀 Uso del Sistema

### Para Usar el Menú de Opciones
```bash
./demo.sh
```

### Para Uso General
```bash
# Opción 1: Menú Python (Recomendado)
python run_system.py

# Opción 2: Menú Docker
./docker-scripts/menu.sh menu

# Opción 3: Inicio Rápido
./start.sh
```

## 📁 Estructura del Proyecto

```
proyecto_distribuidos/
├── actors/                    # Actores (AR, AD, AP)
├── common/                    # Utilidades comunes
├── data/                      # Datos de prueba y configuración
├── ga/                        # Gestor de Almacenamiento
├── gestor_central/            # Gestor Central
├── ps/                        # Proceso Solicitante
├── tools/                     # Herramientas y utilidades
├── docker-scripts/            # Scripts de Docker
├── specs/                     # Especificaciones técnicas
├── demo_profesor.py           # Demostración para profesor
├── demo.sh                    # Script de demostración
├── run_system.py              # Interfaz principal del sistema
└── docker-compose.yml         # Configuración Docker
```

## 🎯 Requisitos Cumplidos

### Primera Entrega (15%)
- ✅ Operaciones RENOVAR y DEVOLVER implementadas
- ✅ Comunicación ZeroMQ (REQ/REP y PUB/SUB)
- ✅ Generación de carga automática desde archivo
- ✅ Distribución en 2 máquinas (simuladas con Docker)
- ✅ Base de datos inicial: 1000 libros, 200 préstamos
- ✅ Logs claros del flujo PS → GC → Actor → GA
- ✅ Respuesta inmediata al PS, procesamiento asíncrono

### Datos Iniciales
- **1000 libros** generados automáticamente
- **200 libros prestados** (50 en sitio A, 150 en sitio B)
- **Campos requeridos**: código, título, disponible
- **Copias idénticas** en ambas sedes

## 🔧 Configuración

### Dependencias
```bash
pip install -r requirements.txt
```

### Variables de Entorno
El sistema usa variables de entorno para configuración:
- Puertos de comunicación ZeroMQ
- Endpoints de conexión
- Modo de operación (serial/threaded)
- Configuración de métricas

### Docker
```bash
# Construir e iniciar sistema completo
docker-compose up -d

# Detener sistema
docker-compose down
```

## 📊 Métricas y Pruebas

### Generación de Carga
- Lectura automática desde `peticiones.txt`
- Múltiples procesos PS simultáneos
- Medición de latencia y throughput
- Generación de gráficos de rendimiento

### Archivo de Peticiones
Formato: `OPERACION CODIGO_LIBRO USUARIO`
```
PRESTAR ISBN-0001 u-1
RENOVAR ISBN-0100 u-17
DEVOLVER ISBN-0099 u-5
```

## 📚 Documentación

- **DEMOSTRACION_PROFESOR.md**: Guía completa del sistema
- **GUIA_DEMOSTRACION.md**: Secuencia paso a paso de uso
- **ENUNCIADO.md**: Requisitos originales del proyecto
- **specs/**: Especificaciones técnicas y contratos

## 🎯 Estado del Proyecto

**Primera Entrega**: ✅ Completada y lista para uso
- Todas las funcionalidades requeridas implementadas
- Sistema funcionando correctamente
- Interfaz interactiva en español disponible
- Documentación completa del sistema

## 🔄 Desarrollo Futuro

El sistema está preparado para:
- Segunda entrega (25%): Operaciones completas, tolerancia a fallas
- Pruebas de rendimiento: Comparación serial vs threaded
- Implementación en máquinas físicas reales
- Optimizaciones de rendimiento

---

**Para usar el sistema: ejecutar `./demo.sh` y seguir las opciones numeradas.**