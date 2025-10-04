Eres un asistente de código. Implementa los componentes de Sebastián del sistema distribuido de biblioteca, compatibles al 100% con el contrato (mensajes, tópicos, puertos) y con los módulos de Alejandro (GC, PS, carga y métricas). Todo debe ser configurable por .env y CLI. Incluye scripts de prueba y ejemplos.

0) Lenguaje, dependencias y estructura
	•	Lenguaje: Python 3.11
	•	Librerías: pyzmq, python-dotenv, pydantic, rich, typer, watchdog (opcional para monitorear archivos), uvloop (opcional Linux)
	•	Estructura de repo (añadiendo a la ya creada por Alejandro):

dist-biblio/
  CONTRACT.md
  .env.example
  requirements.txt

  common/
    __init__.py
    models.py              # reutiliza EXACTAMENTE los esquemas del contrato
    env.py                 # carga de .env con defaults
    logging_utils.py       # logger JSON + modo pretty
    time_utils.py          # now_ms(), today(), add_days()

  actors/
    __init__.py
    renovacion.py          # AR (SUB RENOVACION) -> GA.renovar
    devolucion.py          # AD (SUB DEVOLUCION) -> GA.devolver
    prestamo.py            # AP (REP)           -> GA.checkAndLoan

  ga/
    __init__.py
    server.py              # GA REP: renovar, devolver, checkAndLoan
    storage.py             # lectura/escritura JSON + bloqueo + idempotencia
    oplog.py               # append-only log, lectura incremental
    replication.py         # PUB/SUB de replicación + aplicación idempotente
    health.py              # heartbeat (PUB) y ping (REP opcional)

  tools/
    seed_data.py           # genera books.json inicial y loans.json
    failover_demo.sh       # simula caída del GA primario
    print_subscriber.py    # suscriptor genérico para ver mensajes PUB

  diagrams/                # (opcional) fuentes draw.io
    componentes.drawio
    secuencia_renovacion.drawio
    secuencia_devolucion.drawio
    despliegue.drawio

1) Variables de entorno (.env) — RESPETA NOMBRES del contrato

# --- PUB del GC (para que AR y AD se suscriban)
GC_PUB_CONNECT=tcp://{IP_GC}:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION

# --- AP (Actor Préstamo) — lado servidor REP
AP_REP_BIND=tcp://0.0.0.0:5557

# --- GA (este nodo)
GA_REP_BIND=tcp://0.0.0.0:5560
GA_HEALTH_REP_BIND=tcp://0.0.0.0:5564
GA_HEARTBEAT_PUB_BIND=tcp://0.0.0.0:5565
GA_HEARTBEAT_INTERVAL_MS=2000

# --- Replicación entre GAs (ajustar si este es el nodo B)
GA_REPL_PUB_BIND=tcp://0.0.0.0:5562
GA_REPL_SUB_CONNECT=tcp://{IP_GA_PEER}:5563

# --- Archivos (carpeta local por nodo)
GA_DATA_DIR=./data/siteA
BOOKS_FILE=books.json
LOANS_FILE=loans.json
OPLOG_FILE=oplog.json
APPLIED_INDEX_FILE=applied_index.json
SNAPSHOT_INTERVAL_OPS=500

Si este nodo es B, invierte los puertos/subscripciones (B publica en 5563 y se suscribe a 5562). Debe venir otro .env para B.

2) Esquemas de mensajes (usar common/models.py)

Respeta exactamente:
	•	ActorMessage (desde GC a AR/AD por PUB):

id: str
sedeId: Literal["A","B"]
userId: str
libroCodigo: str
op: Literal["RENOVAR","DEVOLVER"]
dueDateNew: Optional[str]  # solo en RENOVAR


	•	AP <-> GC (REQ/REP):
	•	Request desde GC → AP:

{ "id":"uuid", "libroCodigo":"ISBN-XYZ", "userId":"u-123" }


	•	Respuesta AP → GC (tras consultar GA):

{ "ok": true|false, "reason": Optional[str], "metadata": {"dueDate": "YYYY-MM-DD"} }



3) Actores

3.1 ActorRenovación — actors/renovacion.py
	•	SUB a GC_PUB_CONNECT, tópico TOPIC_RENOVACION.
	•	Por cada mensaje:
	1.	Validar con Pydantic.
	2.	Log: proc=AR stage=recibido id=<id> op=RENOVAR.
	3.	Construir request GA: {id, libroCodigo, userId, dueDateNew}.
	4.	Llamar GA.renovar vía REQ/REP (GA_REP_BIND).
	5.	Log éxito/error (stage=aplicado|error).
	•	CLI:

python -m actors.renovacion --pretty



3.2 ActorDevolución — actors/devolucion.py
	•	SUB a GC_PUB_CONNECT, tópico TOPIC_DEVOLUCION.
	•	Flujo análogo a AR pero llamando GA.devolver.

3.3 ActorPréstamo — actors/prestamo.py
	•	REP en AP_REP_BIND.
	•	Al recibir request {id, libroCodigo, userId}:
	1.	Validar.
	2.	Llamar GA.checkAndLoan (REQ -> GA).
	3.	Mapear respuesta de GA (ok, reason, metadata.dueDate) y devolver al GC.
	4.	Log proc=AP stage=aplicado con ok y dueDate cuando exista.
	•	CLI:

python -m actors.prestamo --pretty



4) GA — servidor de almacenamiento

4.1 ga/storage.py
	•	Maneja lectura/escritura atómica de:
	•	books.json: {codigo, titulo, disponible: bool}
	•	loans.json: {codigo, userId, dueDate, renovaciones}
	•	Operaciones:
	•	renovar(id, codigo, userId, dueDateNew) → valida préstamo activo del user, renovaciones<2, actualiza dueDate y renovaciones+=1.
	•	devolver(id, codigo, userId) → si préstamo activo del user, marca libro disponible, elimina/actualiza loan.
	•	checkAndLoan(id, codigo, userId) → si disponible, crea loan con dueDate = today() + 14 y renovaciones=0.
	•	Cada operación:
	•	Escribe registro en oplog (ver 4.2) con id, op, codigo, userId, timestamps y datos relevantes.
	•	Retorna objeto uniforme: {"ok": bool, "reason": str|None, "metadata": {...}}.

4.2 ga/oplog.py
	•	Append-only de operaciones aplicadas localmente.
	•	Provee lectura incremental (desde applied_index.json) para replicación.
	•	Garantiza idempotencia: si id ya aplicado, ignora (llevar set/índice de ids aplicados).

4.3 ga/replication.py
	•	PUB/SUB entre GA_A y GA_B (asíncrono).
	•	Emite cada entrada nueva del oplog local por PUB.
	•	Escucha del peer y aplica operaciones remotas con el mismo flujo de storage pero marcándolas como “remotas” (no re-emitir para evitar bucles).
	•	Snapshots: cada SNAPSHOT_INTERVAL_OPS consolidar estado para truncar oplog de forma segura.

4.4 ga/health.py
	•	PUB heartbeat cada GA_HEARTBEAT_INTERVAL_MS con {node:"A|B", ts:...}.
	•	REP opcional en GA_HEALTH_REP_BIND que responde “ok” (útil para scripts de verificación).

4.5 ga/server.py
	•	Un REP en GA_REP_BIND que soporte tres métodos:
	•	renovar
	•	devolver
	•	checkAndLoan
	•	Decodifica método por campo method o ruta simple en el payload:

{ "method":"renovar", "payload":{...} }


	•	Usa storage para aplicar, oplog para registrar y replication para publicar.
	•	CLI:

python -m ga.server --data-dir ./data/siteA --pretty
python -m ga.server --data-dir ./data/siteB --pretty



5) Seed de datos y scripts

5.1 tools/seed_data.py
	•	Genera 1000 libros en books.json.
	•	Genera 200 préstamos iniciales (A: 50, B: 150), equilibrando loans.json.
	•	Crea oplog.json vacío y applied_index.json con estructuras mínimas.

CLI:

python tools/seed_data.py --data-dir ./data/siteA
python tools/seed_data.py --data-dir ./data/siteB

5.2 tools/failover_demo.sh
	•	Arranca GA_A y GA_B.
	•	Lanza actores (AR, AD, AP) apuntando a su GA local.
	•	Mata GA_A, verifica que GA_B sigue aplicando operaciones (cuando lleguen por los actores).
	•	Reinicia GA_A y observa cómo se pone al día vía replicación (oplog).

5.3 tools/print_subscriber.py
	•	Suscriptor genérico a un tcp://host:port y un tópico para debug (ej: RENOVACION).

6) Pruebas manuales (sin Alejandro o mientras integra)
	•	Ejecuta AR y AD con print_subscriber.py apuntando al PUB de GC para ver que reciben los tópicos correctos.
	•	Ejecuta AP como REP y prueba con zmq_req simple:

# payload de ejemplo:
{ "id":"test-1", "libroCodigo":"ISBN-0001", "userId":"u-1" }

Debe responder {ok:..., metadata:{dueDate:...}} si disponible.

	•	Ejecuta GA solo y llama métodos con scripts de prueba (REQ) para validar lógica de negocio:
	•	2 renovaciones máximas.
	•	devolución libera el libro.
	•	préstamo falla si no disponible.

7) Compatibilidad estricta con el GC/PS de Alejandro
	•	No cambiar nombres de tópicos: RENOVACION, DEVOLUCION.
	•	AR/AD solo procesan su tipo de operación. Los logs deben mostrarlo claramente.
	•	AP responde exactamente con:

{ "ok": true|false, "reason": "opc", "metadata": { "dueDate": "YYYY-MM-DD" } }


	•	GA es la fuente de verdad: toda validación ocurre ahí.
	•	Idempotencia por id en oplog para evitar aplicar dos veces la misma operación.

8) Calidad, robustez y DX
	•	Timeouts configurables en sockets.
	•	Reintentos leves al peer GA en replicación.
	•	Cierre limpio (SIGINT/SIGTERM).
	•	Logs JSON por línea; --pretty para humanos.
	•	README.md con:
	•	Cómo preparar .env para sitio A y B.
	•	Cómo iniciar GA_A/GA_B, AR/AD/AP.
	•	Cómo probar failover.
	•	Ejemplos de requests para GA y AP.

9) Entregables esperados de esta tarea
	•	Código de AR, AD, AP y GA completo.
	•	.env.example con variables explicadas y dos ejemplos de .env (A y B).
	•	seed_data.py y failover_demo.sh funcionales.
	•	Replicación GA_A ↔ GA_B operativa (con idempotencia).
	•	Logs demostrando:
	•	AR solo maneja renovaciones.
	•	AD solo maneja devoluciones.
	•	AP maneja préstamos con respuesta a GC.
	•	GA aplica operaciones y las replica.
	•	(Opcional) Archivos .drawio base en /diagrams con:
	•	Componentes (PS, GC, AR, AD, AP, GA_A/GA_B).
	•	Secuencias de Renovación y Devolución.
	•	Despliegue (3 máquinas).
