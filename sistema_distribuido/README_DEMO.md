# 🚀 Scripts de Demostración del Sistema Distribuido

## 📋 Scripts Disponibles

### 1. `demo_interactivo.sh` - Demo Paso a Paso
Script interactivo con menú que te permite ejecutar cada paso por separado.

**Características:**
- ✅ Menú interactivo con 8 opciones
- ✅ Explicaciones detalladas de cada paso
- ✅ Análisis de comunicación entre contenedores
- ✅ Mostrar IPs de cada contenedor
- ✅ Logs detallados con colores
- ✅ Pausas entre pasos para explicar

**Uso:**
```bash
./demo_interactivo.sh
```

### 2. `demo_rapido.sh` - Demo Automático
Script que ejecuta todo el proceso automáticamente mostrando la comunicación.

**Características:**
- ✅ Ejecución automática completa
- ✅ Análisis en tiempo real de comunicación
- ✅ Mostrar IPs de contenedores
- ✅ Resumen de cambios en la base de datos
- ✅ Logs de comunicación entre contenedores

**Uso:**
```bash
./demo_rapido.sh
```

## 🎯 Cuándo Usar Cada Script

### Usa `demo_interactivo.sh` cuando:
- Quieras explicar paso a paso
- Necesites pausar entre secciones
- Quieras mostrar la arquitectura del sistema
- Necesites control total sobre la demostración

### Usa `demo_rapido.sh` cuando:
- Quieras una demostración rápida
- El tiempo sea limitado
- Quieras mostrar el flujo completo de una vez
- Necesites un resumen ejecutivo

## 📡 Qué Muestra la Comunicación

Los scripts muestran claramente:

1. **PS → GC**: Solicitudes enviadas (REQ/REP)
2. **GC → PS**: Respuestas inmediatas (REQ/REP)
3. **GC → Actores**: Eventos publicados (PUB/SUB)
4. **Actores → BD**: Actualizaciones de la base de datos

## 🔍 Información Técnica Mostrada

- **IPs de contenedores** para verificar conectividad
- **Patrones de comunicación** (REQ/REP y PUB/SUB)
- **Timestamps** de cada operación
- **Estados de la base de datos** antes y después
- **Estadísticas de procesamiento** (éxito, errores, etc.)

## 🛠️ Requisitos

- Docker y Docker Compose instalados
- Python 3 para formatear JSON
- Terminal con soporte para colores

## 🚨 Notas Importantes

- Los scripts limpian el entorno antes de ejecutar
- Se muestran las IPs reales de los contenedores
- La comunicación se analiza en tiempo real
- Los logs se filtran para mostrar solo lo relevante
- El sistema se puede limpiar con `docker compose down`

## 📊 Ejemplo de Salida

```
📡 PS → GC: Solicitud #1 enviada: {"op": "RENOVACION", "libro_id": "L001"...}
📡 GC → PS: Respuesta recibida: {"status": "OK", "message": "Recibido..."}
📡 GC → Actor: Evento enviado a actores - Topic: renovacion
✅ Actor Ren: Renovación procesada exitosamente (#1)
```

## 🎯 Puntos Clave para la Demostración

1. **Comunicación distribuida** entre contenedores
2. **Patrones ZeroMQ** implementados correctamente
3. **Procesamiento asíncrono** de eventos
4. **Consistencia de datos** en la base de datos
5. **Logs detallados** con timestamps
6. **Arquitectura escalable** y robusta
