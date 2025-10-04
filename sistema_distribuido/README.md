# Sistema Distribuido de Préstamo de Libros

## 📚 Descripción

Este proyecto implementa un sistema distribuido de préstamo de libros usando **ZeroMQ** para la comunicación entre procesos y **Docker** para la distribución. El sistema soporta operaciones de **RENOVACIÓN** y **DEVOLUCIÓN** de libros.

## 🏗️ Arquitectura

El sistema está compuesto por 4 contenedores Docker que simulan computadoras independientes:

- **Gestor de Carga (GC)**: Servicio central que recibe solicitudes y coordina eventos
- **Proceso Solicitante (PS)**: Cliente que envía solicitudes de renovación/devolución
- **Actor de Devolución**: Procesa eventos de devolución y actualiza ejemplares disponibles
- **Actor de Renovación**: Procesa eventos de renovación y actualiza fechas de devolución

## 🔌 Patrones de Comunicación

- **REQ/REP**: Comunicación síncrona entre PS y GC
- **PUB/SUB**: Comunicación asíncrona entre GC y los Actores

## 🚀 Instalación y Ejecución

### Prerrequisitos

- Docker
- Docker Compose

### Ejecutar el Sistema

```bash
# Construir y ejecutar todos los contenedores
docker compose up --build

# Ejecutar en segundo plano
docker compose up --build -d

# Ver logs de todos los servicios
docker compose logs -f

# Detener el sistema
docker compose down
```

## 📁 Estructura del Proyecto

```
sistema_distribuido/
├── gestor_carga.py          # Gestor central de carga
├── proceso_solicitante.py   # Cliente que envía solicitudes
├── actor_devolucion.py      # Actor para devoluciones
├── actor_renovacion.py      # Actor para renovaciones
├── data/
│   ├── libros.json          # Base de datos de libros
│   └── solicitudes.txt      # Archivo de solicitudes
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Imagen Docker
├── docker-compose.yml      # Configuración de contenedores
└── README.md              # Este archivo
```

## 📊 Flujo de Operaciones

1. **PS** lee solicitudes desde `data/solicitudes.txt`
2. **PS** envía solicitudes JSON a **GC** vía REQ/REP
3. **GC** responde inmediatamente con confirmación
4. **GC** publica eventos a los **Actores** vía PUB/SUB
5. **Actores** procesan eventos y actualizan `data/libros.json`

## 🔧 Configuración

### Puertos

- **5001**: REQ/REP entre PS y GC
- **5002**: PUB/SUB entre GC y Actores

### Archivos de Datos

- `data/libros.json`: Base de datos de libros con ejemplares y fechas
- `data/solicitudes.txt`: Lista de operaciones a procesar

## 📝 Formato de Solicitudes

Cada línea en `data/solicitudes.txt` debe tener el formato:
```
OPERACION LIBRO_ID USUARIO_ID [SEDE]
```

Ejemplo:
```
RENOVACION L001 U001
DEVOLUCION L002 U002
```

## 🧪 Pruebas

El sistema incluye datos de prueba en `data/solicitudes.txt` con 6 operaciones mixtas de renovación y devolución.

## 📈 Monitoreo

Todos los servicios generan logs detallados con:
- Timestamps UTC
- Contadores de operaciones
- Estados de conexión
- Errores y advertencias

## 🔍 Verificación

Para verificar que el sistema funciona correctamente:

1. Ejecutar `docker compose up --build`
2. Observar los logs de cada contenedor
3. Verificar que `data/libros.json` se actualiza correctamente
4. Confirmar que todas las operaciones se procesan exitosamente

## 🛠️ Desarrollo

### Estructura de Mensajes

**Solicitud (PS → GC)**:
```json
{
  "op": "RENOVACION|DEVOLUCION",
  "libro_id": "L001",
  "usuario_id": "U001",
  "sede": "SEDE_1"
}
```

**Respuesta (GC → PS)**:
```json
{
  "status": "OK|ERROR",
  "message": "Descripción",
  "operacion": "RENOVACION",
  "libro_id": "L001"
}
```

**Evento (GC → Actores)**:
```json
{
  "operacion": "RENOVACION|DEVOLUCION",
  "libro_id": "L001",
  "usuario_id": "U001",
  "sede": "SEDE_1",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "nueva_fecha_devolucion": "2025-02-03"  // Solo para renovaciones
}
```

## 📋 Características Técnicas

- ✅ Comunicación TCP entre contenedores
- ✅ Manejo de errores robusto
- ✅ Logs detallados con timestamps
- ✅ Base de datos JSON persistente
- ✅ Sistema completamente distribuido
- ✅ Patrones ZeroMQ implementados correctamente
- ✅ Configuración Docker optimizada
