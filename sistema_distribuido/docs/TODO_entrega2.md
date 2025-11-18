# TODO y Gaps Identificados - Entrega 2

## Verificación de Alineación con Enunciado

### ✅ Procesos Obligatorios
- [x] **PS (Proceso Solicitante)**: Implementado en `proceso_solicitante.py`
- [x] **GC (Gestor de Carga)**: Implementado en `gestor_carga.py`
- [x] **GA (Gestor de Almacenamiento)**: Implementado en `gestor_almacenamiento.py`
- [x] **Actores**: 
  - [x] Actor de Préstamo (`actor_prestamo.py`)
  - [x] Actor de Devolución (`actor_devolucion.py`)
  - [x] Actor de Renovación (`actor_renovacion.py`)

### ✅ Patrones de Comunicación
- [x] **REQ/REP (Síncrono)**:
  - [x] PS ↔ GC (puerto 5001)
  - [x] GC ↔ Actor Préstamo (puerto 5004)
  - [x] Actores ↔ GA (puerto 5003)
- [x] **PUB/SUB (Asíncrono)**:
  - [x] GC → Actores (puerto 5002) para devolución y renovación

### ✅ Datos Iniciales
- [x] Base de datos con **1000 libros** ✓
- [x] **200 ejemplares prestados** distribuidos en 2 sedes ✓
  - [x] 50 en SEDE_1
  - [x] 150 en SEDE_2
- [x] Generación automática con `generar_datos_iniciales.py` ✓

### ✅ Operaciones
- [x] **Préstamo**: Síncrono (REQ/REP) con actualización garantizada en BD ✓
- [x] **Devolución**: Asíncrono (ACK inmediato + PUB/SUB) ✓
- [x] **Renovación**: Asíncrono (ACK inmediato + PUB/SUB) ✓

### ✅ Réplicas y Failover
- [x] Réplica primaria y secundaria en GA ✓
- [x] Replicación asíncrona de primaria a secundaria ✓
- [x] Health checks implementados ✓
- [x] **Failover automático**: Implementado - GA usa réplica secundaria cuando primaria falla ✓

### ⚠️ Gaps Identificados y Resueltos

#### 1. Failover GA/BD (RESUELTO)
- **Problema**: El sistema no usaba la réplica secundaria cuando la primaria fallaba
- **Solución**: Implementado failover automático en `gestor_almacenamiento.py`
  - `_cargar_base_datos()` ahora intenta primaria primero, luego secundaria
  - `_guardar_base_datos()` guarda en secundaria si primaria no está disponible
  - Health check indica estado "degraded" cuando solo secundaria está disponible

#### 2. Experimentos de Rendimiento (RESUELTO)
- **Problema**: No existían scripts automatizados para experimentos
- **Solución**: Creado `experimentos_rendimiento.py`
  - Ejecuta experimentos con modo serial y multithread
  - Diferentes configuraciones de PS (4, 6, 10)
  - Genera reportes en Markdown y JSON

#### 3. Documentación (EN PROGRESO)
- **Problema**: Documentación incompleta para entrega 2
- **Solución**: 
  - Mejorar README.md
  - Actualizar docs/pruebas.md
  - Actualizar docs/metricas.md
  - Crear docs/informe_rendimiento_borrador.md
  - Crear docs/resumen_entrega2.md

#### 4. Docstrings y Comentarios (EN PROGRESO)
- **Problema**: Algunos archivos carecen de docstrings completos
- **Solución**: Agregar docstrings a todos los archivos principales

## Checklist de Requisitos de Entrega 2

### Código
- [x] Todos los procesos obligatorios implementados
- [x] Patrones de comunicación correctos (REQ/REP y PUB/SUB)
- [x] Datos iniciales con 1000 libros y 200 ejemplares prestados
- [x] Operaciones síncronas y asíncronas según especificación
- [x] Réplicas primaria y secundaria
- [x] Failover automático GA/BD
- [x] Sistema de métricas implementado
- [x] Modo serial y multithread en GC

### Documentación
- [ ] README.md actualizado con instrucciones completas
- [ ] docs/pruebas.md actualizado
- [ ] docs/metricas.md actualizado
- [ ] docs/informe_rendimiento_borrador.md creado
- [ ] docs/resumen_entrega2.md creado
- [ ] docs/arquitectura.md actualizado con información de failover

### Experimentos
- [x] Script de experimentos creado (`experimentos_rendimiento.py`)
- [ ] Experimentos ejecutados y resultados documentados
- [ ] Reporte de rendimiento generado

### Calidad de Código
- [ ] Docstrings agregados a todos los archivos principales
- [ ] Comentarios explicativos donde sea necesario
- [ ] Código revisado y refactorizado

## Notas Adicionales

### Mejoras Implementadas
1. **Failover GA/BD**: El sistema ahora puede continuar operando usando la réplica secundaria cuando la primaria falla
2. **Health Checks Mejorados**: El health check ahora indica claramente si el sistema está "healthy", "degraded" o "unhealthy"
3. **Scripts de Experimentos**: Automatización completa de experimentos de rendimiento

### Pendientes
1. Ejecutar experimentos y generar resultados reales
2. Completar documentación faltante
3. Agregar docstrings a todos los archivos
4. Revisar y mejorar comentarios en código

