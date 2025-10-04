# Sistema Distribuido de Biblioteca

Este proyecto implementa un sistema distribuido de biblioteca con componentes desarrollados por Alejandro siguiendo el contrato funcional especificado.

## Arquitectura

El sistema está compuesto por:

- **PS (Proceso Solicitante)**: Cliente que envía solicitudes (renovar, devolver, prestar)
- **GC (Gestor Central)**: Recibe solicitudes de PS, las enruta a los actores correctos
- **AR (Actor Renovación)**: Procesa renovaciones (desarrollado por Sebastián)
- **AD (Actor Devolución)**: Procesa devoluciones (desarrollado por Sebastián)
- **AP (Actor Préstamo)**: Procesa préstamos (desarrollado por Sebastián)
- **GA (Gestor de Almacenamiento)**: CRUD sobre libros y préstamos (desarrollado por Sebastián)

## Componentes de Alejandro

Este repositorio contiene los componentes desarrollados por Alejandro:

- **GC Server**: Servidor central con modos serial y threaded
- **PS Client**: Cliente solicitante con medición de latencia
- **Load Generator**: Generador de carga con múltiples PS
- **Charts Generator**: Generador de gráficos de métricas
- **Demo Script**: Script de demostración completa

## Instalación

### 1. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con las IPs reales de las máquinas
```

## 🚀 Quick Start

**The easiest way to use the system is through our menu interfaces:**

```bash
# Option 1: Python Menu Interface (Recommended)
python run_system.py

# Option 2: Docker Menu Interface  
./docker-scripts/menu.sh menu

# Option 3: Quick Start Script
./start.sh
```

**📖 For detailed usage instructions, see [USAGE_GUIDE.md](USAGE_GUIDE.md)**

---

## Uso

### Variables de Entorno

Las siguientes variables pueden configurarse en `.env`:

```bash
# GC Configuration
GC_BIND=tcp://0.0.0.0:5555
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION

# Connections
GC_PUB_CONNECT=tcp://127.0.0.1:5556
AP_REQ_CONNECT=tcp://127.0.0.1:5557

# GC Mode
GC_MODE=serial  # o threaded

# Metrics
METRICS_CSV=metrics/results.csv
MEASUREMENT_WINDOW_SEC=120
```

### 1. Ejecutar GC Server

**Modo Serial:**
```bash
python -m gc.server --mode serial --pretty
```

**Modo Threaded:**
```bash
python -m gc.server --mode threaded --workers 8 --pretty
```

**Con Mock AP (para pruebas sin Sebastián):**
```bash
python -m gc.server --mode serial --mock-ap --pretty
```

### 2. Ejecutar PS Client

```bash
python -m ps.client --sede A --file data/ejemplos/peticiones_sample.txt --pretty
```

Opciones:
- `--sede`: Sitio (A o B)
- `--file`: Archivo de peticiones
- `--gc`: Endpoint del GC
- `--pretty`: Logging bonito
- `--delay`: Delay entre requests (ms)

### 3. Generar Carga

```bash
python tools/spawn_ps.py \
    --ps-per-site 4 \
    --sites A,B \
    --duration-sec 120 \
    --file data/ejemplos/peticiones_sample.txt \
    --gc tcp://127.0.0.1:5555 \
    --mode serial \
    --out metrics/results.csv
```

### 4. Generar Gráficos

```bash
python tools/charts.py --csv metrics/results.csv --outdir metrics/
```

### 5. Demo Completo

```bash
./tools/demo.sh
# o con modo threaded:
./tools/demo.sh threaded
```

## Formato de Peticiones

El archivo `peticiones.txt` debe tener el formato:

```
PRESTAR ISBN-0001 u-1
RENOVAR ISBN-0100 u-17
DEVOLVER ISBN-0099 u-5
```

Donde:
- **PRESTAR**: Solicitar préstamo de libro
- **RENOVAR**: Renovar préstamo existente
- **DEVOLVER**: Devolver libro prestado
- **ISBN-XXXX**: Código del libro
- **u-XX**: ID del usuario

## Esquemas de Mensajes

### PS → GC (solicitud)
```json
{
  "id": "uuid-unique",
  "sedeId": "A|B",
  "userId": "u-123",
  "op": "RENOVAR|DEVOLVER|PRESTAR",
  "libroCodigo": "ISBN-XYZ",
  "timestamp": 1710000000000
}
```

### GC → PS (respuesta)
```json
// Para RENOVAR/DEVOLVER
{ "id": "uuid-unique", "status": "RECIBIDO" }

// Para PRESTAR
{ "id": "uuid-unique", "status": "OK|ERROR", "reason": "opcional", "dueDate": "2025-10-31" }
```

### GC → Actores (PUB)
```json
{
  "id": "uuid-unique",
  "sedeId": "A|B",
  "userId": "u-123",
  "libroCodigo": "ISBN-XYZ",
  "op": "RENOVAR|DEVOLVER",
  "dueDateNew": "2025-11-07"  // solo en RENOVAR
}
```

## Métricas

El sistema genera métricas en formato CSV con las siguientes columnas:

- `timestamp`: Timestamp de la medición
- `ps_per_site`: Número de PS por sitio
- `mode`: Modo del GC (serial/threaded)
- `site`: Sitio (A/B)
- `avg_ms`: Latencia promedio de PRESTAR (ms)
- `stdev_ms`: Desviación estándar de latencia (ms)
- `count_2min`: Cantidad de PRESTAR exitosos en 2 minutos

## Logging

El sistema usa logging JSON estandarizado:

```json
{ "ts": 1710000000000, "proc": "GC|PS", "id": "uuid", "op": "RENOVAR|DEVOLVER|PRESTAR",
  "stage": "recibido|enviado|aplicado|error", "detail": "texto" }
```

Usar `--pretty` para formato legible.

## Pruebas Manuales

### Sin Sebastián (Mock AP)

1. **Iniciar GC con mock:**
```bash
python -m gc.server --mode serial --mock-ap --pretty
```

2. **Ejecutar PS client:**
```bash
python -m ps.client --sede A --file data/ejemplos/peticiones_sample.txt --pretty
```

3. **Verificar logs:**
- Para RENOVAR/DEVOLVER: respuesta RECIBIDO + publicación en tópicos
- Para PRESTAR: status=OK y dueDate presente

4. **Ejecutar carga:**
```bash
python tools/spawn_ps.py --ps-per-site 2 --duration-sec 30 --mode serial
```

5. **Generar gráficos:**
```bash
python tools/charts.py --csv metrics/results.csv --outdir metrics/
```

## Compatibilidad con Sebastián

El sistema está diseñado para integrarse con los componentes de Sebastián:

- **Tópicos fijos**: `RENOVACION`, `DEVOLUCION`
- **ActorMessage**: Formato exacto según contrato
- **AP Connection**: `AP_REQ_CONNECT` para préstamos
- **Variables de entorno**: Todas las IPs/puertos configurables

## Estructura del Proyecto

```
dist-biblio/
├── common/                    # Utilidades comunes
│   ├── models.py             # Esquemas Pydantic
│   ├── env.py                # Configuración de entorno
│   ├── logging_utils.py      # Logging JSON + pretty
│   └── time_utils.py         # Utilidades de tiempo
├── gc/                       # Gestor Central
│   ├── server.py             # Servidor principal
│   ├── router.py             # Lógica de enrutamiento
│   └── modes.py              # Modos serial/threaded
├── ps/                       # Proceso Solicitante
│   ├── client.py             # Cliente PS
│   └── workload.py           # Generador de carga
├── tools/                    # Herramientas
│   ├── spawn_ps.py           # Generador de carga
│   ├── charts.py             # Generador de gráficos
│   └── demo.sh               # Script de demo
├── data/ejemplos/            # Datos de ejemplo
│   └── peticiones_sample.txt # Archivo de peticiones
├── metrics/                  # Métricas y gráficos
│   ├── results.csv           # CSV de métricas
│   ├── latency_vs_ps.png     # Gráfico de latencia
│   └── throughput_vs_ps.png  # Gráfico de throughput
├── requirements.txt          # Dependencias Python
├── .env.example             # Variables de entorno
└── README.md                # Este archivo
```

## Troubleshooting

### Error de conexión ZMQ
- Verificar que los puertos estén disponibles
- Comprobar configuración de `.env`
- Asegurar que GC esté ejecutándose antes que PS

### Timeout en PS
- Verificar que GC esté respondiendo
- Comprobar conectividad de red
- Revisar logs del GC

### Métricas vacías
- Verificar que haya requests PRESTAR en el archivo
- Comprobar que la duración sea suficiente
- Revisar logs de PS para errores

## Desarrollo

### Agregar nuevas operaciones
1. Actualizar `common/models.py` con nuevos esquemas
2. Modificar `gc/router.py` para manejar la nueva operación
3. Actualizar `ps/client.py` si es necesario
4. Agregar tests en `data/ejemplos/peticiones_sample.txt`

### Modificar métricas
1. Actualizar `tools/spawn_ps.py` para recopilar nuevas métricas
2. Modificar `tools/charts.py` para visualizar nuevas métricas
3. Actualizar documentación

## Licencia

Este proyecto es parte de un trabajo académico de sistemas distribuidos.
