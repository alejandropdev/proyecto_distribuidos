# CONTRATO.md — Sistema Distribuido de Biblioteca
**Equipo:** Alejandro (GC, PS, Carga, Métricas, Presentación) • Sebastián (Actores, GA, Replicación, Diagramas)  
**Fecha:** _(completar)_

> Este documento define **acuerdos obligatorios** para que ambos podamos desarrollar en paralelo **sin bloqueos**. Cualquier cambio aquí debe anunciarse antes de codificar.

---

## 1) Arquitectura y procesos
**Procesos:**  
- **PS (Proceso Solicitante):** cliente que envía solicitudes (renovar, devolver, prestar). _Múltiples instancias por carga._  
- **GC (Gestor Central):** recibe solicitudes de PS, las enruta al actor correcto y responde.  
- **AR (Actor Renovación):** procesa renovaciones.  
- **AD (Actor Devolución):** procesa devoluciones.  
- **AP (Actor Préstamo):** procesa préstamos (chequea disponibilidad).  
- **GA (Gestor de Almacenamiento):** CRUD simple sobre libros y préstamos (archivo JSON). Puede tener 2 instancias (primaria/secundaria) con replicación.

**Topología (3 máquinas):**
- **Sitio A:** GC + AR + AD + AP + GA_A
- **Sitio B:** GC + AR + AD + AP + GA_B
- **Máquina 3:** Solo PS (generador de carga lanza N PS para A y para B)

**Transporte:** **ZeroMQ**  
- PS ⇄ GC: **REQ/REP** (sincrónico)  
- GC → AR/AD: **PUB/SUB** (asíncrono, tópicos)  
- GC ⇄ AP: **REQ/REP** (sincrónico)  
- Actores/GC ⇄ GA: **REQ/REP** (sincrónico)  
- GA_A ⇄ GA_B: **PUSH/PULL** o **PUB/SUB** para replicación (asíncrono)

---

## 2) Direcciones y puertos (completar IPs reales)
Definir IPs en `.env` en cada máquina.

```
# GC (entrada de PS)
GC_BIND=tcp://0.0.0.0:5555

# PUB de GC (salida hacia actores)
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION

# Actores se suscriben al PUB de GC
AR_SUB_CONNECT=tcp://{IP_GC}:5556
AD_SUB_CONNECT=tcp://{IP_GC}:5556

# GC ⇄ AP (préstamo)
AP_REP_BIND=tcp://0.0.0.0:5557
AP_REQ_CONNECT=tcp://{IP_AP}:5557

# GA (sitio A y B)
GA_A_REP_BIND=tcp://0.0.0.0:5560
GA_B_REP_BIND=tcp://0.0.0.0:5561

# Replicación entre GA
GA_A_REPL_PUB_BIND=tcp://0.0.0.0:5562
GA_B_REPL_SUB_CONNECT=tcp://{IP_GA_A}:5562
GA_B_REPL_PUB_BIND=tcp://0.0.0.0:5563
GA_A_REPL_SUB_CONNECT=tcp://{IP_GA_B}:5563
```

---

## 3) Esquemas de mensajes (JSON)
### 3.1 Mensaje PS → GC (solicitud)
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

### 3.2 GC → PS (respuesta inmediata)
- Para `RENOVAR` / `DEVOLVER`: confirmación de recibido.
```json
{ "id": "uuid-unique", "status": "RECIBIDO" }
```
- Para `PRESTAR`: respuesta final del AP (sincrónica).
```json
{ "id": "uuid-unique", "status": "OK|ERROR", "reason": "opcional", "dueDate": "2025-10-31" }
```

### 3.3 GC → Actores (PUB, con tópico)
- **Tópicos fijos:** `RENOVACION`, `DEVOLUCION`
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

### 3.4 Actores ⇄ GA (REQ/REP)
- **AR → GA.renovar**
```json
{ "id":"uuid", "libroCodigo":"ISBN-XYZ", "userId":"u-123", "dueDateNew":"2025-11-07" }
```
- **AD → GA.devolver**
```json
{ "id":"uuid", "libroCodigo":"ISBN-XYZ", "userId":"u-123" }
```
- **AP → GA.prestar / GA.checkAndLoan**
```json
{ "id":"uuid", "libroCodigo":"ISBN-XYZ", "userId":"u-123" }
```
- **Respuesta GA (genérica)**
```json
{ "ok": true, "reason": null, "metadata": { "dueDate": "2025-10-31" } }
```

---

## 4) Reglas de negocio mínimas
- **RENOVAR:** solo si el libro está prestado al `userId`. Máx. 2 renovaciones por préstamo. `dueDateNew = dueDate + 7 días`.  
- **DEVOLVER:** marca el libro como disponible; limpia contador de renovaciones.  
- **PRESTAR:** solo si disponible; `dueDate = hoy + 14 días`.  
- Validaciones se hacen en **GA** (fuente de verdad).

---

## 5) GA — almacenamiento, formato y replicación
**Archivos por sitio:** `books.json`, `loans.json`, `oplog.json`  
**Estructura mínima:**
```json
// books.json (por libro)
{ "codigo":"ISBN-XYZ", "titulo":"...", "disponible": true }

// loans.json (por préstamo activo)
{
  "codigo":"ISBN-XYZ",
  "userId":"u-123",
  "dueDate":"2025-10-31",
  "renovaciones": 1
}

// oplog.json (apéndice solo-forward para replicación)
{ "ts":1710000000001, "id":"uuid", "op":"DEVOLVER", "codigo":"ISBN-XYZ", "userId":"u-123" }
```

**Replicación asíncrona:**  
- GA escribe cada operación en `oplog.json` y la **publica** al otro GA.  
- El GA receptor **aplica idempotente** (si `id` ya aplicado, ignora).  
- Heartbeat cada 2s para salud. Si un GA cae, el otro sigue; al volver, se pone al día leyendo los `oplog` faltantes.

---

## 6) Logging estándar (todos los procesos)
Formato JSON por línea:
```json
{ "ts": 1710000000000, "proc": "GC|AR|AD|AP|GA|PS", "id": "uuid", "op": "RENOVAR|DEVOLVER|PRESTAR",
  "stage": "recibido|enviado|aplicado|error", "detail": "texto" }
```
**Objetivo para el demo:** que se vea claramente que **AR** maneja renovaciones y **AD** maneja devoluciones (y **AP** los préstamos).

---

## 7) Generación de carga (PS múltiples)
- Script `spawn_ps` lanza **N PS por sitio** (valores de referencia: 4, 6, 10).  
- Cada PS lee un archivo `peticiones.txt` con mix de operaciones y envía en loop con pequeñas esperas aleatorias.  
- **Ventana de medida:** 2 minutos.  
- **Semillas:** 1000 libros totales; 200 ya prestados al iniciar (A:50, B:150).

Ejemplo `peticiones.txt`:
```
PRESTAR ISBN-0001 u-1
RENOVAR ISBN-0100 u-17
DEVOLVER ISBN-0099 u-5
...
```

---

## 8) Métricas (Tabla 1 del enunciado)
- **Tiempo de préstamo (latencia):** medido en **PS** para cada `PRESTAR` (`t_respuesta - t_envío`).  
- **Stdev de latencia de préstamo:** desviación estándar de esas muestras.  
- **Cantidad de préstamos en 2 min:** total de `PRESTAR` con `status=OK` en la ventana.  
- Guardar en CSV: `ps_por_sitio, modo_gc, avg_ms, stdev_ms, count_2min, timestamp`.

**Experimento base:** comparar **GC en modo serial vs multihilo** (flag `--mode=serial|threaded`).

---

## 9) Casos de prueba y criterios de aceptación
1. **Renovación individual:** PS envía → GC confirma recibido → AR registra → GA actualiza `dueDate`.  
   - _Éxito:_ logs muestran `proc=AR stage=aplicado id=...` y `dueDate` aumentado 7 días.
2. **Devolución individual:** PS envía → GC confirma → AD registra → GA marca disponible.  
   - _Éxito:_ logs con `proc=AD stage=aplicado` y `disponible=true`.
3. **Préstamo individual:** PS envía → GC reenvía a AP → AP/GA confirman → PS recibe `OK`.  
   - _Éxito:_ `status=OK`, `dueDate` = hoy+14.
4. **Carga mezclada:** 2+ PS activos intercalando operaciones.  
   - _Éxito:_ se ven AR y AD recibiendo solo su tipo; métricas generadas.
5. **Replicación:** ejecutar en A, verificar estado en B tras unos segundos.  
   - _Éxito:_ `books.json` y `loans.json` convergen.
6. **Falla GA primario:** matar GA_A en medio de carga; procesos cambian a GA_B.  
   - _Éxito:_ sistema continúa; al volver GA_A, se sincroniza por `oplog`.

---

## 10) Presentación (máx. 5 diapositivas)
1. **Componentes:** PS, GC, AR, AD, AP, GA (A/B), conexiones.  
2. **Secuencia Renovación:** PS→GC→AR→GA (y confirmaciones).  
3. **Secuencia Devolución:** PS→GC→AD→GA.  
4. **Carga y Métricas:** cómo generamos carga y cómo medimos.  
5. **Resultados y conclusiones:** tabla/gráfico + 2–3 bullets.

---

## 11) División de trabajo (resumen)
- **Alejandro:** GC, PS, generador de carga, métricas, presentación (texto y gráficos).  
- **Sebastián:** AR, AD, AP, GA, replicación y salud, diagramas (componentes y secuencias).

---

## 12) Calendario sugerido
- **Día 1:** Fase 1 (este contrato) + iniciar GC y GA.  
- **Día 2:** Actores y PS básicos.  
- **Día 3:** Carga, métricas, replicación.  
- **Día 4:** Integración, pruebas, diagramas.  
- **Día 5:** Presentación y ensayo.

---

## 13) Checklist de integración
- [ ] `.env` con IPs reales en las 3 máquinas  
- [ ] GC escucha PS y publica a tópicos correctos  
- [ ] AR/AD suscritos y logueando recepción  
- [ ] AP respondiendo a GC (préstamos)  
- [ ] GA leyendo/escribiendo JSON y replicando  
- [ ] Script de carga ejecuta 4/6/10 PS por sitio  
- [ ] CSV de métricas generado  
- [ ] Demo script: caso simple + carga + falla GA + resultados

---

## 14) Notas finales
- **Idempotencia:** todas las operaciones llevan `id` único; GA ignora duplicados.  
- **Tiempos:** usar milisegundos UNIX en todos los `ts`.  
- **Riesgos:** saturación de disco por `oplog` → truncar por ventana, con snapshot periódico.
