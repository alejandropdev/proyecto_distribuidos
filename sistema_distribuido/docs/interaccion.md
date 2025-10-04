# Secuencias de Interacción - Sistema Distribuido de Préstamo de Libros

## 🔄 Flujo General del Sistema

El sistema sigue un patrón de comunicación híbrido:
1. **Síncrono**: PS ↔ GC (REQ/REP) para confirmación inmediata
2. **Asíncrono**: GC → Actores (PUB/SUB) para procesamiento distribuido

## 📤 Secuencia: RENOVACIÓN de Libro

### 1. Inicio de Operación
```
PS lee línea: "RENOVACION L001 U001"
PS construye JSON: {
  "op": "RENOVACION",
  "libro_id": "L001", 
  "usuario_id": "U001",
  "sede": "SEDE_1"
}
```

### 2. Comunicación REQ/REP (PS → GC)
```
PS (REQ) ──────────────────► GC (REP)
     │                           │
     │ JSON Request              │
     ├──────────────────────────►│
     │                           │ Parse JSON
     │                           │ Validate operation
     │                           │ Generate timestamp
     │                           │ Calculate new date (+7 days)
     │                           │
     │ JSON Response             │
     │◄──────────────────────────┤
     │ {                         │
     │   "status": "OK",         │
     │   "message": "Recibido.   │
     │   Procesando...",         │
     │   "operacion": "RENOVACION",│
     │   "libro_id": "L001"      │
     │ }                         │
     │                           │
```

**Tiempo**: < 500ms (ACK inmediato)

### 3. Publicación Asíncrona (GC → Actor Renovación)
```
GC (PUB) ──────────────────► Actor Renovación (SUB)
     │                           │
     │ Topic: "renovacion"       │
     │ Event: {                  │
     │   "operacion": "RENOVACION",│
     │   "libro_id": "L001",     │
     │   "usuario_id": "U001",   │
     │   "sede": "SEDE_1",       │
     │   "timestamp": "2025-01-27T10:30:00.000Z",│
     │   "nueva_fecha_devolucion": "2025-02-03"│
     │ }                         │
     ├──────────────────────────►│
     │                           │ Receive event
     │                           │ Load libros.json
     │                           │ Find book L001
     │                           │ Update fecha_devolucion
     │                           │ Save libros.json
     │                           │ Log success
```

**Tiempo**: 1-3 segundos (procesamiento asíncrono)

### 4. Actualización de Base de Datos
```json
// Antes
{
  "libro_id": "L001",
  "titulo": "1984",
  "ejemplares_disponibles": 2,
  "fecha_devolucion": "2025-01-27"
}

// Después
{
  "libro_id": "L001", 
  "titulo": "1984",
  "ejemplares_disponibles": 2,
  "fecha_devolucion": "2025-02-03"  // +7 días
}
```

## 📥 Secuencia: DEVOLUCIÓN de Libro

### 1. Inicio de Operación
```
PS lee línea: "DEVOLUCION L002 U002"
PS construye JSON: {
  "op": "DEVOLUCION",
  "libro_id": "L002",
  "usuario_id": "U002", 
  "sede": "SEDE_1"
}
```

### 2. Comunicación REQ/REP (PS → GC)
```
PS (REQ) ──────────────────► GC (REP)
     │                           │
     │ JSON Request              │
     ├──────────────────────────►│
     │                           │ Parse JSON
     │                           │ Validate operation
     │                           │ Generate timestamp
     │                           │
     │ JSON Response             │
     │◄──────────────────────────┤
     │ {                         │
     │   "status": "OK",         │
     │   "message": "Recibido.   │
     │   Procesando...",         │
     │   "operacion": "DEVOLUCION",│
     │   "libro_id": "L002"      │
     │ }                         │
     │                           │
```

**Tiempo**: < 500ms (ACK inmediato)

### 3. Publicación Asíncrona (GC → Actor Devolución)
```
GC (PUB) ──────────────────► Actor Devolución (SUB)
     │                           │
     │ Topic: "devolucion"       │
     │ Event: {                  │
     │   "operacion": "DEVOLUCION",│
     │   "libro_id": "L002",     │
     │   "usuario_id": "U002",   │
     │   "sede": "SEDE_1",       │
     │   "timestamp": "2025-01-27T10:31:00.000Z"│
     │ }                         │
     ├──────────────────────────►│
     │                           │ Receive event
     │                           │ Load libros.json
     │                           │ Find book L002
     │                           │ Increment ejemplares_disponibles
     │                           │ Save libros.json
     │                           │ Log success
```

**Tiempo**: 1-3 segundos (procesamiento asíncrono)

### 4. Actualización de Base de Datos
```json
// Antes
{
  "libro_id": "L002",
  "titulo": "El Principito", 
  "ejemplares_disponibles": 1,
  "fecha_devolucion": "2025-01-28"
}

// Después
{
  "libro_id": "L002",
  "titulo": "El Principito",
  "ejemplares_disponibles": 2,  // +1
  "fecha_devolucion": "2025-01-28"
}
```

## ❌ Secuencia: Operación Inválida

### 1. Solicitud Inválida
```
PS envía: {
  "op": "OPERACION_INVALIDA",
  "libro_id": "L999",
  "usuario_id": "U999"
}
```

### 2. Manejo de Error
```
PS (REQ) ──────────────────► GC (REP)
     │                           │
     │ JSON Request              │
     ├──────────────────────────►│
     │                           │ Parse JSON
     │                           │ Validate operation
     │                           │ Detect invalid operation
     │                           │
     │ JSON Response             │
     │◄──────────────────────────┤
     │ {                         │
     │   "status": "ERROR",      │
     │   "message": "Operación   │
     │   inválida: OPERACION_    │
     │   INVALIDA. Solo se       │
     │   permiten RENOVACION     │
     │   y DEVOLUCION"           │
     │ }                         │
     │                           │
```

**Comportamiento**:
- ✅ GC responde con ERROR
- ✅ No se publica evento
- ✅ No se actualiza BD
- ✅ GC no crashea

## 🔄 Flujo Completo con Múltiples Operaciones

### Archivo de Solicitudes
```
RENOVACION L001 U001
DEVOLUCION L002 U002  
RENOVACION L003 U003
DEVOLUCION L001 U004
RENOVACION L002 U005
DEVOLUCION L003 U006
```

### Timeline de Ejecución
```
T+0s    PS inicia lectura de archivo
T+1s    PS envía RENOVACION L001 → GC ACK → Actor Renovación
T+2s    PS envía DEVOLUCION L002 → GC ACK → Actor Devolución  
T+3s    PS envía RENOVACION L003 → GC ACK → Actor Renovación
T+4s    PS envía DEVOLUCION L001 → GC ACK → Actor Devolución
T+5s    PS envía RENOVACION L002 → GC ACK → Actor Renovación
T+6s    PS envía DEVOLUCION L003 → GC ACK → Actor Devolución
T+7s    PS termina procesamiento
```

### Estado Final de Base de Datos
```json
[
  {
    "libro_id": "L001",
    "titulo": "1984", 
    "ejemplares_disponibles": 3,  // +1 por devolución
    "fecha_devolucion": "2025-02-03"  // +7 días por renovación
  },
  {
    "libro_id": "L002",
    "titulo": "El Principito",
    "ejemplares_disponibles": 2,  // +1 por devolución  
    "fecha_devolucion": "2025-02-03"  // +7 días por renovación
  },
  {
    "libro_id": "L003", 
    "titulo": "Cien Años de Soledad",
    "ejemplares_disponibles": 1,  // +1 por devolución
    "fecha_devolucion": "2025-02-03"  // +7 días por renovación
  }
]
```

## 🔍 Puntos de Observación

### Logs del PS
```
2025-01-27 10:30:00 - PS - INFO - 📤 Solicitud #1 enviada: {"op": "RENOVACION", ...}
2025-01-27 10:30:00 - PS - INFO - 📥 Respuesta recibida: {"status": "OK", ...}
2025-01-27 10:30:00 - PS - INFO - ✅ Solicitud procesada exitosamente
```

### Logs del GC
```
2025-01-27 10:30:00 - GC - INFO - 📨 Solicitud recibida: {"op": "RENOVACION", ...}
2025-01-27 10:30:00 - GC - INFO - 📡 Evento enviado a actores - Topic: renovacion
2025-01-27 10:30:00 - GC - INFO - 📝 Operación #1 procesada: RENOVACION - Libro L001
```

### Logs del Actor Renovación
```
2025-01-27 10:30:01 - ACTOR_REN - INFO - 📨 Evento recibido - Topic: renovacion
2025-01-27 10:30:01 - ACTOR_REN - INFO - 📚 Libro L001 renovado por usuario U001
2025-01-27 10:30:01 - ACTOR_REN - INFO - ✅ Renovación procesada exitosamente (#1)
```

### Logs del Actor Devolución
```
2025-01-27 10:30:02 - ACTOR_DEV - INFO - 📨 Evento recibido - Topic: devolucion
2025-01-27 10:30:02 - ACTOR_DEV - INFO - 📚 Libro L002 devuelto por usuario U002
2025-01-27 10:30:02 - ACTOR_DEV - INFO - ✅ Devolución procesada exitosamente (#1)
```

## ⚡ Optimizaciones de Rendimiento

### Paralelización
- **REQ/REP**: Síncrono, no paralelizable
- **PUB/SUB**: Asíncrono, actores procesan en paralelo
- **Base de datos**: Acceso secuencial por archivo

### Timeouts y Reintentos
- **ACK timeout**: 5 segundos
- **Event timeout**: 3 segundos  
- **File change timeout**: 10 segundos
- **Reintentos**: No implementados (fail-fast)

### Monitoreo de Salud
- **Health checks**: Cada 30 segundos
- **Logs continuos**: Todos los servicios
- **Métricas**: Latencia, throughput, errores

## 🚨 Casos de Error

### GC No Disponible
```
PS (REQ) ──────────────────► GC (REP)
     │                           │
     │ JSON Request              │
     ├──────────────────────────►│
     │                           │ [TIMEOUT]
     │                           │
     │ [TIMEOUT ERROR]           │
     │◄──────────────────────────┤
```

**Manejo**: PS registra error y continúa con siguiente solicitud

### Actor No Disponible
```
GC (PUB) ──────────────────► Actor (SUB)
     │                           │
     │ Event                     │ [NO CONECTADO]
     ├──────────────────────────►│
     │                           │
     │ [EVENTO PERDIDO]          │
```

**Manejo**: Evento se pierde, no hay reintento automático

### Error en Base de Datos
```
Actor ─────────────────────► libros.json
     │                           │
     │ Write                     │
     ├──────────────────────────►│
     │                           │ [PERMISSION DENIED]
     │                           │
     │ [ERROR]                   │
     │◄──────────────────────────┤
```

**Manejo**: Actor registra error, operación falla

## 📊 Métricas de Interacción

### Latencia por Componente
- **PS → GC**: < 500ms
- **GC → Actor**: < 100ms (publicación)
- **Actor → BD**: < 200ms (escritura)
- **Total end-to-end**: 1-3 segundos

### Throughput
- **Solicitudes/segundo**: 1 (limitado por sleep)
- **Eventos/segundo**: 1-2 (dependiendo del tipo)
- **Actualizaciones BD/segundo**: 1

### Confiabilidad
- **Tasa de éxito ACK**: 100%
- **Tasa de recepción eventos**: 100%
- **Tasa de actualización BD**: 100%
- **Tiempo de recuperación**: < 30 segundos
