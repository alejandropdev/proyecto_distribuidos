# 📚 Sistema Distribuido de Préstamo de Libros

## 🎯 Descripción del Proyecto

Este proyecto implementa un **sistema distribuido de préstamo de libros** usando **ZeroMQ** para la comunicación entre procesos y **Docker** para la distribución. El sistema soporta operaciones de **RENOVACIÓN** y **DEVOLUCIÓN** de libros con una arquitectura completamente distribuida.

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por **4 contenedores Docker** que simulan computadoras independientes:

- **🔄 Gestor de Carga (GC)**: Servicio central que recibe solicitudes y coordina eventos
- **📤 Proceso Solicitante (PS)**: Cliente que envía solicitudes de renovación/devolución
- **📚 Actor de Devolución**: Procesa eventos de devolución y actualiza ejemplares disponibles
- **📅 Actor de Renovación**: Procesa eventos de renovación y actualiza fechas de devolución

## 🔌 Patrones de Comunicación

- **REQ/REP (Síncrono)**: Comunicación entre PS y GC (puerto 5001)
- **PUB/SUB (Asíncrono)**: Comunicación entre GC y los Actores (puerto 5002)

## 🚀 Cómo Ejecutar el Sistema

### Opción 1: Demo Interactivo (Recomendado para presentaciones)

```bash
cd sistema_distribuido
./demo_interactivo.sh
```

**Características:**
- ✅ Menú interactivo con 8 opciones
- ✅ Control total sobre cada paso
- ✅ Análisis detallado de comunicación entre contenedores
- ✅ Mostrar IPs de cada contenedor
- ✅ Pausas entre pasos para explicar
- ✅ Logs con colores para mejor visualización

### Opción 2: Demo Rápido (Para demostraciones rápidas)

```bash
cd sistema_distribuido
./demo_rapido.sh
```

**Características:**
- ✅ Ejecución automática completa
- ✅ Análisis en tiempo real de comunicación
- ✅ Resumen ejecutivo de todo el proceso
- ✅ Ideal para demostraciones rápidas

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

## 📊 Flujo de Operaciones

1. **PS** lee solicitudes desde `data/solicitudes.txt`
2. **PS** envía solicitudes JSON a **GC** vía REQ/REP
3. **GC** responde inmediatamente con confirmación
4. **GC** publica eventos a los **Actores** vía PUB/SUB
5. **Actores** procesan eventos y actualizan `data/libros.json`

## 📁 Estructura del Proyecto

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

## 📝 Formato de Solicitudes

Cada línea en `data/solicitudes.txt` debe tener el formato:
```
OPERACION LIBRO_ID USUARIO_ID [SEDE]
```

**Ejemplo:**
```
RENOVACION L001 U001
DEVOLUCION L002 U002
```

## 🔧 Configuración

### Puertos
- **5001**: REQ/REP entre PS y GC
- **5002**: PUB/SUB entre GC y Actores

### Archivos de Datos
- `data/libros.json`: Base de datos de libros con ejemplares y fechas
- `data/solicitudes.txt`: Lista de operaciones a procesar

## 📈 Monitoreo y Logs

Todos los servicios generan logs detallados con:
- Timestamps UTC
- Contadores de operaciones
- Estados de conexión
- Errores y advertencias
- Análisis de comunicación entre contenedores

## 🧪 Datos de Prueba

El sistema incluye datos de prueba en `data/solicitudes.txt` con **6 operaciones mixtas**:
- 3 renovaciones (L001, L003, L002)
- 3 devoluciones (L002, L001, L003)

## 📊 Ejemplo de Resultados

**Estado inicial:**
```json
[
  {"libro_id": "L001", "ejemplares_disponibles": 6},
  {"libro_id": "L002", "ejemplares_disponibles": 4},
  {"libro_id": "L003", "ejemplares_disponibles": 8}
]
```

**Estado final (después de procesar):**
```json
[
  {"libro_id": "L001", "ejemplares_disponibles": 7},  // +1 devolución
  {"libro_id": "L002", "ejemplares_disponibles": 5},  // +1 devolución
  {"libro_id": "L003", "ejemplares_disponibles": 9}   // +1 devolución
]
```

## 🔍 Verificación del Sistema

Para verificar que el sistema funciona correctamente:

1. Ejecutar `./demo_interactivo.sh` o `./demo_rapido.sh`
2. Observar los logs de cada contenedor
3. Verificar que `data/libros.json` se actualiza correctamente
4. Confirmar que todas las operaciones se procesan exitosamente
5. Analizar la comunicación entre contenedores

## 🛠️ Requisitos

- **Docker** y **Docker Compose**
- **Python 3** (para formatear JSON)
- **Terminal** con soporte para colores

## 📋 Características Técnicas

- ✅ Comunicación TCP entre contenedores
- ✅ Manejo de errores robusto
- ✅ Logs detallados con timestamps
- ✅ Base de datos JSON persistente
- ✅ Sistema completamente distribuido
- ✅ Patrones ZeroMQ implementados correctamente
- ✅ Configuración Docker optimizada
- ✅ Scripts de demostración interactivos

## 🎯 Puntos Clave para Demostración

1. **Comunicación distribuida** entre contenedores
2. **Patrones ZeroMQ** (REQ/REP y PUB/SUB) implementados correctamente
3. **Procesamiento asíncrono** de eventos
4. **Consistencia de datos** en la base de datos
5. **Logs detallados** con análisis de comunicación
6. **Arquitectura escalable** y robusta

## 🚨 Notas Importantes

- Los scripts limpian el entorno antes de ejecutar
- Se muestran las IPs reales de los contenedores
- La comunicación se analiza en tiempo real
- Los logs se filtran para mostrar solo lo relevante
- El sistema se puede limpiar con `docker compose down`

---

**Desarrollado como proyecto de Sistemas Distribuidos**  
*Implementando patrones de comunicación ZeroMQ con Docker*
