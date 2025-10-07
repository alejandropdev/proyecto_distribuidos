# Sistema Distribuido de Préstamo de Libros

## Descripción del Proyecto

Este proyecto implementa un **sistema distribuido de préstamo de libros** usando **ZeroMQ** para la comunicación entre procesos y **Docker** para la distribución. El sistema soporta operaciones de **RENOVACIÓN** y **DEVOLUCIÓN** de libros con una arquitectura completamente distribuida.

## Arquitectura del Sistema

El sistema está compuesto por **4 contenedores Docker** que simulan computadoras independientes:

- **Gestor de Carga (GC)**: Servicio central que recibe solicitudes y coordina eventos
- **Proceso Solicitante (PS)**: Cliente que envía solicitudes de renovación/devolución
- **Actor de Devolución**: Procesa eventos de devolución y actualiza ejemplares disponibles
- **Actor de Renovación**: Procesa eventos de renovación y actualiza fechas de devolución

## Patrones de Comunicación

- **REQ/REP (Síncrono)**: Comunicación entre PS y GC (puerto 5001)
- **PUB/SUB (Asíncrono)**: Comunicación entre GC y los Actores (puerto 5002)

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

# 1. Levantar servicios principales
docker compose up --build -d gc actor_devolucion actor_renovacion

# 2. Ejecutar solicitudes
docker compose run --rm ps

# 3. Ver logs
docker compose logs

# 4. Detener sistema
docker compose down
```

## Flujo de Operaciones

1. **PS** lee solicitudes desde `data/solicitudes.txt`
2. **PS** envía solicitudes JSON a **GC** vía REQ/REP
3. **GC** responde inmediatamente con confirmación
4. **GC** publica eventos a los **Actores** vía PUB/SUB
5. **Actores** procesan eventos y actualizan `data/libros.json`

## Estructura del Proyecto

```
proyecto_distribuidos/
├── README.md                    # Este archivo
├── Enunciado.pdf               # Enunciado del proyecto
└── sistema_distribuido/
    ├── gestor_carga.py          # Gestor central de carga
    ├── proceso_solicitante.py   # Cliente que envía solicitudes
    ├── actor_devolucion.py      # Actor para devoluciones
    ├── actor_renovacion.py      # Actor para renovaciones
    ├── demo_interactivo.sh      # Script de demo paso a paso
    ├── demo_rapido.sh           # Script de demo automático
    ├── data/
    │   ├── libros.json          # Base de datos de libros
    │   └── solicitudes.txt      # Archivo de solicitudes
    ├── requirements.txt         # Dependencias Python
    ├── Dockerfile              # Imagen Docker
    └── docker-compose.yml      # Configuración de contenedores
```

## Formato de Solicitudes

Cada línea en `data/solicitudes.txt` debe tener el formato:
```
OPERACION LIBRO_ID USUARIO_ID SEDE
```

**Ejemplo:**
```
RENOVACION L0001 U0231 SEDE_1
DEVOLUCION L0002 U0456 SEDE_2
```

**Operaciones soportadas:**
- `RENOVACION`: Extiende la fecha de devolución (+7 días)
- `DEVOLUCION`: Marca el ejemplar como disponible

**Sedes soportadas:**
- `SEDE_1`: Primera sede (50 ejemplares prestados inicialmente)
- `SEDE_2`: Segunda sede (150 ejemplares prestados inicialmente)

## Configuración

### Puertos
- **5001**: REQ/REP entre PS y GC
- **5002**: PUB/SUB entre GC y Actores

### Archivos de Datos
- `data/libros.json`: Base de datos de libros con ejemplares y fechas
- `data/solicitudes.txt`: Lista de operaciones a procesar

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

## Cumplimiento de Requerimientos

### Datos Iniciales ✅
- ✅ **1000 libros** en la base de datos
- ✅ **200 ejemplares prestados** (50 en SEDE_1, 150 en SEDE_2)
- ✅ **Separación por sedes** implementada
- ✅ **Sistema de ejemplares individuales** con fechas de devolución
- ✅ **Libros con un único ejemplar** (102 libros)
- ✅ **Copia idéntica** de la BD en ambas sedes

### Funcionalidades Implementadas ✅
- ✅ **Solicitud de operaciones** de devolución y renovación desde PS hasta Actores
- ✅ **3 procesos** ubicados en al menos dos computadoras distintas (Docker)
- ✅ **Mecanismo para generar requerimientos** (lectura de archivo)
- ✅ **Comunicación distribuida** con ZeroMQ
- ✅ **Patrones REQ/REP y PUB/SUB** implementados correctamente

## Requisitos del Sistema

- **Docker** y **Docker Compose**
- **Python 3** (para scripts de verificación y generación de datos)
- **Terminal** con soporte para colores

## Características Técnicas

- **Comunicación TCP** entre contenedores
- **Manejo de errores** robusto
- **Logs detallados** con timestamps
- **Base de datos JSON** persistente con estructura completa
- **Sistema completamente distribuido** con 4 contenedores
- **Patrones ZeroMQ** implementados correctamente (REQ/REP y PUB/SUB)
- **Configuración Docker** optimizada
- **Scripts de demostración** interactivos
- **Sistema de ejemplares individuales** con fechas de devolución
- **Separación por sedes** con contadores independientes

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
