# Resumen de Entrega 2 - Sistema Distribuido de Préstamo de Libros

## Cumplimiento de Requisitos del Enunciado

### ✅ Procesos Obligatorios

- [x] **PS (Proceso Solicitante)**: Implementado en `proceso_solicitante.py`
  - Lee solicitudes desde archivos de texto
  - Envía solicitudes a GC vía REQ/REP
  - Registra métricas de rendimiento

- [x] **GC (Gestor de Carga)**: Implementado en `gestor_carga.py`
  - Recibe solicitudes de PS vía REQ/REP (puerto 5001)
  - Procesa préstamos de forma síncrona (REQ/REP con Actor Préstamo)
  - Publica eventos de devolución/renovación vía PUB/SUB (puerto 5002)
  - Soporta modo serial y multithread

- [x] **GA (Gestor de Almacenamiento)**: Implementado en `gestor_almacenamiento.py`
  - Gestiona base de datos con réplicas primaria y secundaria
  - Proporciona operaciones vía REQ/REP (puerto 5003)
  - Implementa failover automático a réplica secundaria

- [x] **Actores**:
  - [x] Actor de Préstamo (`actor_prestamo.py`): Procesa préstamos síncronamente
  - [x] Actor de Devolución (`actor_devolucion.py`): Procesa devoluciones asíncronamente
  - [x] Actor de Renovación (`actor_renovacion.py`): Procesa renovaciones asíncronamente

### ✅ Patrones de Comunicación

- [x] **REQ/REP (Síncrono)**:
  - PS ↔ GC (puerto 5001): Todas las solicitudes
  - GC ↔ Actor Préstamo (puerto 5004): Solicitudes de préstamo
  - Actores ↔ GA (puerto 5003): Operaciones de base de datos

- [x] **PUB/SUB (Asíncrono)**:
  - GC → Actores (puerto 5002): Eventos de devolución y renovación
  - Topics: `devolucion`, `renovacion`

### ✅ Datos Iniciales

- [x] **1000 libros** en la base de datos
- [x] **200 ejemplares prestados** distribuidos en 2 sedes:
  - 50 ejemplares en SEDE_1
  - 150 ejemplares en SEDE_2
- [x] Generación automática con `generar_datos_iniciales.py`

### ✅ Operaciones

- [x] **Préstamo**: 
  - Síncrono (REQ/REP)
  - Actualización garantizada en BD
  - Máximo 2 semanas de préstamo

- [x] **Devolución**: 
  - Asíncrono (ACK inmediato + PUB/SUB)
  - Procesamiento por Actor de Devolución

- [x] **Renovación**: 
  - Asíncrono (ACK inmediato + PUB/SUB)
  - Extiende fecha de devolución (+7 días)
  - Procesamiento por Actor de Renovación

### ✅ Réplicas y Failover

- [x] **Réplica Primaria**: `data/primary/libros.json`
- [x] **Réplica Secundaria**: `data/secondary/libros.json`
- [x] **Replicación Asíncrona**: Primaria → Secundaria
- [x] **Failover Automático**: GA usa réplica secundaria cuando primaria falla
- [x] **Health Checks**: Implementados en GA y actores

### ✅ Opción A: Serial vs Multihilos

- [x] **Modo Serial**: 
  - Procesamiento secuencial en un solo thread
  - Configuración: `GC_MODE=serial`

- [x] **Modo Multithread**: 
  - Procesamiento concurrente con múltiples workers
  - Configuración: `GC_MODE=multithread`, `GC_WORKERS=N`
  - Cada worker tiene su propio socket REQ hacia Actor Préstamo

### ✅ Sistema de Métricas

- [x] **Registro de métricas**: `logs/metricas.csv`
- [x] **Métricas registradas**:
  - Tiempo de respuesta (ms)
  - Desviación estándar
  - Préstamos procesados en 2 minutos
  - Tasa de éxito

### ✅ Experimentos de Rendimiento

- [x] **Script automatizado**: `experimentos_rendimiento.py`
- [x] **Experimentos configurados**:
  - Modo serial vs multithread
  - Diferentes cantidades de PS (4, 6, 10)
  - Duración de 2 minutos por experimento
- [x] **Reportes generados**:
  - `logs/reporte_rendimiento.md`
  - `logs/resultados_experimentos.json`

## Pruebas Implementadas

### Suite de Pruebas Automatizadas

El sistema incluye pruebas automatizadas usando pytest:

1. **test_end_to_end.py**: 
   - Valida comunicación REQ/REP y PUB/SUB
   - Verifica actualización de base de datos
   - Mide latencia ACK (< 500ms)

2. **test_pubsub_visibility.py**: 
   - Verifica recepción de eventos PUB/SUB
   - Valida estructura de eventos
   - Confirma tasa de recepción 100%

3. **test_file_workload.py**: 
   - Valida procesamiento completo de archivo de solicitudes
   - Verifica coherencia entre PS y GC
   - Analiza cambios en base de datos

### Cómo Ejecutar las Pruebas

```bash
cd sistema_distribuido
make test
# O manualmente:
docker compose up -d ga gc actor_prestamo actor_devolucion actor_renovacion
docker compose run --rm tester python -m pytest -v tests/
```

Para más detalles, ver `docs/pruebas.md`.

## Experimentos de Rendimiento

### Ejecutar Experimentos

```bash
cd sistema_distribuido
python experimentos_rendimiento.py
```

### Configuración de Experimentos

El script ejecuta automáticamente 6 experimentos:

1. Serial con 4 PS (2 SEDE_1 + 2 SEDE_2)
2. Serial con 6 PS (3 SEDE_1 + 3 SEDE_2)
3. Serial con 10 PS (5 SEDE_1 + 5 SEDE_2)
4. Multithread con 4 PS (2 SEDE_1 + 2 SEDE_2)
5. Multithread con 6 PS (3 SEDE_1 + 3 SEDE_2)
6. Multithread con 10 PS (5 SEDE_1 + 5 SEDE_2)

### Resultados

Los resultados se generan automáticamente en:
- `logs/reporte_rendimiento.md`: Reporte completo en Markdown
- `logs/resultados_experimentos.json`: Resultados en formato JSON
- `logs/metricas.csv`: Métricas detalladas

Para más información, ver `docs/informe_rendimiento_borrador.md`.

## Tolerancia a Fallas

### Failover de Réplica Primaria

El sistema implementa failover automático cuando la réplica primaria falla:

1. **Detección**: GA detecta que la primaria no está disponible
2. **Conmutación**: Automáticamente usa la réplica secundaria
3. **Estado**: Health check indica estado "degraded"
4. **Recuperación**: Cuando la primaria se restaura, el sistema vuelve a modo "healthy"

### Cómo Demostrar Failover

```bash
# 1. Iniciar sistema
cd sistema_distribuido
docker compose up -d ga gc actor_prestamo

# 2. Simular fallo de réplica primaria
mv data/primary/libros.json data/primary/libros.json.backup

# 3. Verificar health check
docker compose exec ga python -c "
from gestor_almacenamiento import GestorAlmacenamiento
ga = GestorAlmacenamiento()
health = ga.health_check()
print('Estado:', health['status'])
print('Usando secundaria:', health['using_secondary'])
"

# 4. Probar operaciones (deberían funcionar con secundaria)
docker compose run --rm ps

# 5. Restaurar primaria
cp data/secondary/libros.json data/primary/libros.json
```

### Failover de GA (Servicio)

Los actores implementan health checks periódicos hacia GA:

- Detectan cuando GA no responde
- Registran advertencias en logs
- Reintentan conexión automáticamente
- Se reconectan cuando GA se recupera

Para más detalles, ver `docs/arquitectura.md`.

## Estructura del Proyecto

```
sistema_distribuido/
├── gestor_carga.py              # GC - Modo serial y multithread
├── gestor_almacenamiento.py     # GA - Réplicas y failover
├── proceso_solicitante.py       # PS - Cliente
├── actor_prestamo.py            # Actor de Préstamo
├── actor_devolucion.py          # Actor de Devolución
├── actor_renovacion.py          # Actor de Renovación
├── metricas.py                 # Sistema de métricas
├── utils_failover.py           # Utilidades de failover
├── generar_datos_iniciales.py  # Generador de datos
├── experimentos_rendimiento.py # Script de experimentos
├── data/
│   ├── libros.json             # Base de datos principal
│   ├── primary/
│   │   └── libros.json         # Réplica primaria
│   ├── secondary/
│   │   └── libros.json         # Réplica secundaria
│   └── solicitudes.txt         # Archivo de solicitudes
├── logs/
│   ├── metricas.csv            # Métricas de rendimiento
│   ├── reporte_rendimiento.md  # Reporte de experimentos
│   └── resultados_experimentos.json
├── tests/                      # Suite de pruebas
│   ├── test_end_to_end.py
│   ├── test_pubsub_visibility.py
│   └── test_file_workload.py
└── docs/
    ├── arquitectura.md         # Arquitectura del sistema
    ├── pruebas.md              # Documentación de pruebas
    ├── metricas.md             # Documentación de métricas
    ├── informe_rendimiento_borrador.md
    ├── resumen_entrega2.md    # Este archivo
    └── TODO_entrega2.md        # Gaps identificados
```

## Documentación

### Archivos de Documentación

- **README.md**: Documentación principal del proyecto
- **docs/arquitectura.md**: Arquitectura detallada del sistema
- **docs/pruebas.md**: Documentación de pruebas automatizadas
- **docs/metricas.md**: Sistema de métricas y análisis
- **docs/informe_rendimiento_borrador.md**: Borrador del informe de rendimiento
- **docs/resumen_entrega2.md**: Este resumen

## Características Técnicas Implementadas

### Comunicación
- ✅ ZeroMQ REQ/REP para comunicación síncrona
- ✅ ZeroMQ PUB/SUB para comunicación asíncrona
- ✅ Comunicación TCP entre contenedores Docker

### Base de Datos
- ✅ Réplicas primaria y secundaria
- ✅ Replicación asíncrona
- ✅ Failover automático

### Rendimiento
- ✅ Modo serial y multithread
- ✅ Sistema de métricas
- ✅ Experimentos automatizados

### Robustez
- ✅ Health checks
- ✅ Manejo de errores
- ✅ Reconexión automática

## Checklist Final

- [x] Todos los procesos obligatorios implementados
- [x] Patrones de comunicación correctos
- [x] Datos iniciales según especificación
- [x] Operaciones síncronas y asíncronas
- [x] Réplicas y failover
- [x] Modo serial y multithread
- [x] Sistema de métricas
- [x] Experimentos de rendimiento
- [x] Pruebas automatizadas
- [x] Documentación completa

## Notas Finales

Este sistema cumple con todos los requisitos de la Entrega 2 del proyecto de Sistemas Distribuidos. El código está documentado, probado y listo para demostración.

Para ejecutar el sistema completo:

```bash
cd sistema_distribuido
python generar_datos_iniciales.py
docker compose up --build -d
```

Para más información, consultar el README.md principal.

