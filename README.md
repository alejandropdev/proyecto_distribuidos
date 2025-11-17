# Sistema Distribuido de Préstamo de Libros - Etapa 2

## Descripción del Proyecto

Este proyecto implementa un **sistema distribuido de préstamo de libros** usando **ZeroMQ** para la comunicación entre procesos y **Docker** para la distribución. El sistema soporta operaciones de **PRÉSTAMO**, **RENOVACIÓN** y **DEVOLUCIÓN** de libros con una arquitectura completamente distribuida, réplicas de base de datos y failover automático.

## Arquitectura del Sistema

El sistema está compuesto por **6 contenedores Docker** que simulan computadoras independientes:

- **Gestor de Almacenamiento (GA)**: Gestiona la base de datos con réplicas primaria y secundaria
- **Gestor de Carga (GC)**: Servicio central que recibe solicitudes y coordina eventos
- **Proceso Solicitante (PS)**: Cliente que envía solicitudes de préstamo, renovación y devolución
- **Actor de Préstamo**: Procesa solicitudes de préstamo de forma síncrona
- **Actor de Devolución**: Procesa eventos de devolución y actualiza ejemplares disponibles
- **Actor de Renovación**: Procesa eventos de renovación y actualiza fechas de devolución

## Patrones de Comunicación

- **REQ/REP (Síncrono)**: 
  - PS ↔ GC (puerto 5001) - Todas las solicitudes
  - GC ↔ Actor Préstamo (puerto 5004) - Solicitudes de préstamo
  - Actores ↔ GA (puerto 5003) - Operaciones de base de datos
- **PUB/SUB (Asíncrono)**: 
  - GC → Actores (puerto 5002) - Eventos de devolución y renovación

## Cómo Ejecutar el Sistema

### Opción 1: Demo Interactivo (Recomendado para presentaciones)

```bash
cd sistema_distribuido
./demo_interactivo.sh
```

**Características:**
- Menú interactivo con 8 opciones
- Control total sobre cada paso
- Análisis detallado de comunicación entre contenedores
- Mostrar IPs de cada contenedor
- Pausas entre pasos para explicar
- Logs con colores para mejor visualización

### Opción 2: Demo Rápido (Para demostraciones rápidas)

```bash
cd sistema_distribuido
./demo_rapido.sh
```

**Características:**
- Ejecución automática completa
- Análisis en tiempo real de comunicación
- Resumen ejecutivo de todo el proceso
- Ideal para demostraciones rápidas

### Opción 3: Ejecución Manual

```bash
cd sistema_distribuido

# 1. Generar datos iniciales (si no existen)
python generar_datos_iniciales.py

# 2. Levantar servicios principales
docker compose up --build -d ga gc actor_prestamo actor_devolucion actor_renovacion

# 3. Esperar a que los servicios estén listos
sleep 5

# 4. Ejecutar solicitudes
docker compose run --rm ps

# 5. Ver logs
docker compose logs

# 6. Detener sistema
docker compose down
```

### Inicialización de Datos

Antes de ejecutar el sistema por primera vez, es necesario generar los datos iniciales:

```bash
cd sistema_distribuido
python generar_datos_iniciales.py
```

Esto creará:
- `data/libros.json` - Base de datos principal
- `data/primary/libros.json` - Réplica primaria
- `data/secondary/libros.json` - Réplica secundaria

Las tres réplicas estarán sincronizadas inicialmente.

## Flujo de Operaciones

### Préstamo (REQ/REP Síncrono)

1. **PS** lee solicitud de préstamo desde `data/solicitudes.txt`
2. **PS** envía solicitud JSON a **GC** vía REQ/REP (puerto 5001)
3. **GC** reenvía la solicitud a **Actor Préstamo** vía REQ/REP (puerto 5004)
4. **Actor Préstamo** consulta **GA** para validar disponibilidad vía REQ/REP (puerto 5003)
5. **GA** actualiza réplica primaria y replica asíncronamente a secundaria
6. **Actor Préstamo** responde a **GC** con resultado
7. **GC** responde a **PS** con resultado final
8. **PS** registra métricas de tiempo de respuesta

### Devolución/Renovación (PUB/SUB Asíncrono)

1. **PS** lee solicitud desde `data/solicitudes.txt`
2. **PS** envía solicitud JSON a **GC** vía REQ/REP (puerto 5001)
3. **GC** responde inmediatamente con confirmación
4. **GC** publica evento a los **Actores** correspondientes vía PUB/SUB (puerto 5002)
5. **Actor** (Devolución/Renovación) recibe evento y consulta **GA** vía REQ/REP
6. **GA** actualiza réplica primaria y replica asíncronamente a secundaria

## Estructura del Proyecto

```
proyecto_distribuidos/
├── README.md                    # Este archivo
├── Enunciado.pdf               # Enunciado del proyecto
└── sistema_distribuido/
    ├── gestor_almacenamiento.py # Gestor de almacenamiento (GA)
    ├── gestor_carga.py          # Gestor central de carga (GC)
    ├── proceso_solicitante.py   # Cliente que envía solicitudes (PS)
    ├── actor_prestamo.py        # Actor para préstamos
    ├── actor_devolucion.py      # Actor para devoluciones
    ├── actor_renovacion.py      # Actor para renovaciones
    ├── metricas.py              # Sistema de métricas
    ├── utils_failover.py        # Utilidades de failover
    ├── generar_datos_iniciales.py # Generador de datos iniciales
    ├── demo_interactivo.sh      # Script de demo paso a paso
    ├── demo_rapido.sh           # Script de demo automático
    ├── data/
    │   ├── libros.json          # Base de datos principal
    │   ├── primary/
    │   │   └── libros.json      # Réplica primaria
    │   ├── secondary/
    │   │   └── libros.json      # Réplica secundaria
    │   └── solicitudes.txt      # Archivo de solicitudes
    ├── logs/
    │   └── metricas.csv         # Métricas de rendimiento
    ├── requirements.txt         # Dependencias Python
    ├── Dockerfile              # Imagen Docker
    └── docker-compose.yml      # Configuración de contenedores
```

## Formato de Solicitudes

Cada línea en `data/solicitudes.txt` debe tener el formato:
```
OPERACION LIBRO_ID USUARIO_ID SEDE [search_criteria]
```

**Ejemplos:**
```
PRESTAMO L0001 U0231 SEDE_1
PRESTAMO None U0231 SEDE_1 titulo:Quijote
RENOVACION L0001 U0231 SEDE_1
DEVOLUCION L0002 U0456 SEDE_2
```

**Operaciones soportadas:**
- `PRESTAMO`: Presta un libro a un usuario (máximo 2 semanas)
  - Puede usar `LIBRO_ID` o `None` con `titulo:TITULO` para búsqueda
- `RENOVACION`: Extiende la fecha de devolución (+7 días)
- `DEVOLUCION`: Marca el ejemplar como disponible

**Sedes soportadas:**
- `SEDE_1`: Primera sede (50 ejemplares prestados inicialmente)
- `SEDE_2`: Segunda sede (150 ejemplares prestados inicialmente)

**Criterios de búsqueda (solo para préstamos):**
- `titulo:TITULO`: Busca libro por título (parcial)

## Configuración

### Puertos
- **5001**: REQ/REP entre PS y GC
- **5002**: PUB/SUB entre GC y Actores (devolución/renovación)
- **5003**: REQ/REP entre Actores y GA (operaciones de base de datos)
- **5004**: REQ/REP entre GC y Actor Préstamo

### Archivos de Datos
- `data/libros.json`: Base de datos principal
- `data/primary/libros.json`: Réplica primaria (actualizada primero)
- `data/secondary/libros.json`: Réplica secundaria (replicada asíncronamente)
- `data/solicitudes.txt`: Lista de operaciones a procesar

### Variables de Entorno

Todos los servicios son configurables mediante variables de entorno:

**GA (Gestor de Almacenamiento):**
- `GA_HOST`: Host del socket REP (default: 0.0.0.0)
- `GA_PORT`: Puerto del socket REP (default: 5003)
- `GA_PRIMARY_PATH`: Ruta a réplica primaria (default: data/primary/libros.json)
- `GA_SECONDARY_PATH`: Ruta a réplica secundaria (default: data/secondary/libros.json)

**GC (Gestor de Carga):**
- `GC_HOST`: Host del socket REP (default: 0.0.0.0)
- `GC_REP_PORT`: Puerto REQ/REP (default: 5001)
- `GC_PUB_PORT`: Puerto PUB/SUB (default: 5002)
- `ACTOR_PRESTAMO_HOST`: Host del Actor Préstamo (default: actor_prestamo)
- `ACTOR_PRESTAMO_PORT`: Puerto del Actor Préstamo (default: 5004)
- `GA_HOST`: Host del GA (default: ga)
- `GA_PORT`: Puerto del GA (default: 5003)

**Actores:**
- `GC_HOST`: Host del GC (default: gc)
- `GC_PUB_PORT`: Puerto PUB del GC (default: 5002)
- `GA_HOST`: Host del GA (default: ga)
- `GA_PORT`: Puerto del GA (default: 5003)

**PS (Proceso Solicitante):**
- `GC_HOST`: Host del GC (default: gc)
- `GC_PORT`: Puerto del GC (default: 5001)

## Monitoreo y Logs

Todos los servicios generan logs detallados con:
- Timestamps UTC
- Contadores de operaciones
- Estados de conexión
- Errores y advertencias
- Análisis de comunicación entre contenedores

## Datos Iniciales

El sistema incluye una **base de datos completa** con datos iniciales según los requerimientos:

### Base de Datos de Libros (`data/libros.json`)
- **1000 libros** con títulos realistas
- **7728 ejemplares** en total
- **200 ejemplares prestados** distribuidos por sedes:
  - **50 ejemplares** prestados en **SEDE_1**
  - **150 ejemplares** prestados en **SEDE_2**
- **7528 ejemplares disponibles**
- **102 libros** con un único ejemplar
- **898 libros** con múltiples ejemplares

### Archivo de Solicitudes (`data/solicitudes.txt`)
- **21 solicitudes** de prueba con formato completo
- Operaciones de **RENOVACIÓN** y **DEVOLUCIÓN**
- Solicitudes para ambas sedes (**SEDE_1** y **SEDE_2**)
- Pruebas de casos de error (libros no existentes, usuarios sin préstamos)

## Estructura de Datos

### Base de Datos (`data/libros.json`)
```json
{
  "metadata": {
    "total_libros": 1000,
    "total_ejemplares": 7728,
    "ejemplares_disponibles": 7528,
    "ejemplares_prestados_sede_1": 50,
    "ejemplares_prestados_sede_2": 150
  },
  "libros": [
    {
      "libro_id": "L0001",
      "titulo": "El Quijote",
      "total_ejemplares": 2,
      "ejemplares_disponibles": 0,
      "ejemplares_prestados": 2,
      "ejemplares": [
        {
          "ejemplar_id": "L0001-E001",
          "libro_id": "L0001",
          "titulo": "El Quijote",
          "estado": "prestado",
          "fecha_devolucion": "2025-10-20",
          "usuario_prestamo": "U0231",
          "sede": "SEDE_1"
        }
      ]
    }
  ]
}
```

### Ejemplo de Operación
**Antes de devolución:**
- Ejemplar `L0001-E001` está prestado por usuario `U0231` en `SEDE_1`
- Fecha de devolución: `2025-10-20`

**Después de devolución:**
- Ejemplar `L0001-E001` está disponible
- Contador de disponibles: `0 → 1`
- Contador de prestados: `2 → 1`

## Scripts de Verificación

### Verificación Completa
```bash
cd sistema_distribuido
python verificar_sistema.py
```
Verifica que todos los datos iniciales cumplen con los requerimientos del enunciado.

### Prueba Rápida
```bash
cd sistema_distribuido
python prueba_rapida.py
```
Prueba las funcionalidades básicas del sistema sin usar Docker.

### Generación de Datos
```bash
cd sistema_distribuido
python generar_datos_iniciales.py
```
Regenera los datos iniciales con 1000 libros y 200 ejemplares prestados.

## Pruebas de Failover

El sistema implementa failover automático cuando GA o la réplica primaria falla. Para probar el failover:

### 1. Iniciar el Sistema

```bash
cd sistema_distribuido
docker compose up --build -d ga gc actor_prestamo actor_devolucion actor_renovacion
```

### 2. Simular Fallo de GA

En una terminal separada:

```bash
# Detener GA
docker compose stop ga

# Observar logs de los actores - deberían detectar el fallo
docker compose logs -f actor_prestamo actor_devolucion actor_renovacion
```

Los actores detectarán el fallo mediante health checks y registrarán advertencias en los logs.

### 3. Recuperar GA

```bash
# Reiniciar GA
docker compose start ga

# Los actores deberían reconectarse automáticamente
docker compose logs -f actor_prestamo
```

### 4. Verificar Sincronización

```bash
# Comparar réplicas
diff data/primary/libros.json data/secondary/libros.json
```

Las réplicas deberían estar sincronizadas después de la recuperación.

## Experimentos de Rendimiento

El sistema registra métricas de rendimiento para operaciones de préstamo.

### Ejecutar Experimento de Carga

1. **Preparar archivo de solicitudes con ≥20 préstamos:**

```bash
cd sistema_distribuido
# Crear archivo con múltiples préstamos
cat > data/solicitudes_test.txt << EOF
PRESTAMO L0001 U0001 SEDE_1
PRESTAMO L0002 U0002 SEDE_1
PRESTAMO L0003 U0003 SEDE_1
# ... agregar más líneas
EOF
```

2. **Ejecutar el sistema:**

```bash
docker compose up -d ga gc actor_prestamo
sleep 5
docker compose run --rm -e GC_HOST=gc -e GC_PORT=5001 ps python proceso_solicitante.py data/solicitudes_test.txt
```

3. **Analizar métricas:**

```bash
# Ver métricas en CSV
cat logs/metricas.csv

# O usar Python para análisis
python -c "
import csv
import statistics

with open('logs/metricas.csv', 'r') as f:
    reader = csv.DictReader(f)
    tiempos = [float(row['tiempo_respuesta_ms']) for row in reader if row['operacion'] == 'PRESTAMO']
    
    print(f'Total préstamos: {len(tiempos)}')
    print(f'Tiempo promedio: {statistics.mean(tiempos):.2f} ms')
    print(f'Desviación estándar: {statistics.stdev(tiempos):.2f} ms' if len(tiempos) > 1 else 'N/A')
"
```

### Métricas Registradas

El archivo `logs/metricas.csv` contiene:
- `timestamp`: Fecha y hora de la operación
- `operacion`: Tipo de operación (PRESTAMO)
- `tiempo_respuesta_ms`: Tiempo de respuesta en milisegundos
- `libro_id`: ID del libro
- `exito`: SI/NO si la operación fue exitosa
- `total_prestamos_2min`: Número de préstamos en últimos 2 minutos
- `tiempo_promedio_ms`: Tiempo promedio en ventana de 2 minutos
- `desviacion_estandar_ms`: Desviación estándar en ventana de 2 minutos

## Cumplimiento de Requerimientos - Etapa 2

### Funcionalidades Implementadas ✅

**Operaciones:**
- ✅ **PRESTAMO**: Implementado con REQ/REP síncrono
- ✅ **RENOVACION**: Implementado con PUB/SUB asíncrono
- ✅ **DEVOLUCION**: Implementado con PUB/SUB asíncrono

**Gestor de Almacenamiento (GA):**
- ✅ **Réplicas primaria y secundaria** con sincronización asíncrona
- ✅ **Operaciones**: get_book, loan_book, return_book, renew_book, update_copies
- ✅ **Health checks** para detección de fallos
- ✅ **Replicación asíncrona** automática

**Failover:**
- ✅ **Health checks periódicos** desde actores y GC hacia GA
- ✅ **Detección automática** de fallos
- ✅ **Reconexión automática** cuando GA se recupera

**Métricas:**
- ✅ **Tiempo de respuesta** de préstamos
- ✅ **Desviación estándar** calculada
- ✅ **Préstamos procesados en 2 minutos**
- ✅ **Exportación a CSV**

**Configuración:**
- ✅ **Variables de entorno** para todos los servicios
- ✅ **Configuración distribuida** para múltiples máquinas
- ✅ **Puertos configurables**

**Datos Iniciales:**
- ✅ **1000 libros** en la base de datos
- ✅ **200 ejemplares prestados** (50 en SEDE_1, 150 en SEDE_2)
- ✅ **Réplicas sincronizadas** inicialmente

## Requisitos del Sistema

- **Docker** y **Docker Compose**
- **Python 3** (para scripts de verificación y generación de datos)
- **Terminal** con soporte para colores

## Características Técnicas

- **Comunicación TCP** entre contenedores
- **Manejo de errores** robusto con reintentos
- **Logs detallados** con timestamps en español
- **Base de datos JSON** persistente con estructura completa
- **Sistema completamente distribuido** con 6 contenedores
- **Patrones ZeroMQ** implementados correctamente (REQ/REP y PUB/SUB)
- **Réplicas de base de datos** con sincronización asíncrona
- **Failover automático** con health checks
- **Sistema de métricas** con exportación a CSV
- **Configuración Docker** optimizada con variables de entorno
- **Scripts de demostración** interactivos
- **Sistema de ejemplares individuales** con fechas de devolución
- **Separación por sedes** con contadores independientes
- **Búsqueda de libros** por código o criterios (título, etc.)
- **Validación de préstamos** (máximo 2 semanas)

## Puntos Clave para Demostración

1. **Comunicación distribuida** entre contenedores
2. **Patrones ZeroMQ** (REQ/REP y PUB/SUB) implementados correctamente
3. **Procesamiento asíncrono** de eventos
4. **Consistencia de datos** en la base de datos
5. **Logs detallados** con análisis de comunicación
6. **Arquitectura escalable** y robusta

## Notas Importantes

- Los scripts limpian el entorno antes de ejecutar
- Se muestran las IPs reales de los contenedores
- La comunicación se analiza en tiempo real
- Los logs se filtran para mostrar solo lo relevante
- El sistema se puede limpiar con `docker compose down`

---

**Desarrollado como proyecto de Sistemas Distribuidos**  
*Implementando patrones de comunicación ZeroMQ con Docker*
