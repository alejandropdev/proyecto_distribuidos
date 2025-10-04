Eres un asistente de código. Implementa los componentes de Alejandro del sistema distribuido de biblioteca, siguiendo estrictamente este contrato funcional y de integración. No modifiques los esquemas de mensaje ni los nombres de variables; expón TODO vía CLI y .env para acoplarse con los procesos de Sebastián (Actores + GA).

0) Lenguaje, dependencias y estándares
	•	Lenguaje: Python 3.11
	•	Librerías: pyzmq, python-dotenv, uvloop (opcional Linux), pydantic (validar payload), pandas, matplotlib (charts), rich (logs bonitos), typer (CLI)
	•	Estructura de repo:

dist-biblio/
  CONTRACT.md                         # (ya existe)
  .env.example
  requirements.txt
  common/
    __init__.py
    models.py                         # Pydantic: Request/Reply/Actor payloads
    env.py                            # carga de .env (con defaults)
    logging_utils.py                  # logger JSON + pretty
    time_utils.py                     # milisegundos, now(), etc.
  gc/
    __init__.py
    server.py                         # GC REQ/REP + PUB/SUB + REQ a AP
    router.py                         # lógica de enrutamiento por op
    modes.py                          # Serial vs Threaded
  ps/
    __init__.py
    client.py                         # Cliente PS (REQ/REP con GC)
    workload.py                       # Lector peticiones.txt y generador
  tools/
    spawn_ps.py                       # lanza N PS por sitio y mide 2 min
    charts.py                         # grafica CSV (avg, stdev, throughput)
    demo.sh                           # demo rápida: simple + carga
  data/
    ejemplos/
      peticiones_sample.txt
  metrics/
    results.csv                       # salida de métricas (append)
  README.md

1) Variables de entorno (.env)

Crea .env.example con las mismas claves del contrato (ajustables por Sebastián):

# GC (entrada de PS)
GC_BIND=tcp://0.0.0.0:5555
# PUB de GC (salida hacia actores)
GC_PUB_BIND=tcp://0.0.0.0:5556
TOPIC_RENOVACION=RENOVACION
TOPIC_DEVOLUCION=DEVOLUCION

# Conexiones de actores al PUB del GC (Sebastián fija IP real del GC)
GC_PUB_CONNECT=tcp://{IP_GC}:5556

# GC ⇄ AP (préstamo) — Sebastián fija la IP real del AP
AP_REQ_CONNECT=tcp://127.0.0.1:5557

# Modo de ejecución del GC: serial o threaded
GC_MODE=serial

# Métricas
METRICS_CSV=metrics/results.csv
MEASUREMENT_WINDOW_SEC=120

Nota: no definas puertos de AR/AD aquí; GC solo les publica por GC_PUB_BIND con tópicos.

2) Esquemas de mensajes (respeta al 100%)

common/models.py (Pydantic)
	•	ClientRequest:

id: str            # uuid
sedeId: Literal["A","B"]
userId: str
op: Literal["RENOVAR","DEVOLVER","PRESTAR"]
libroCodigo: str
timestamp: int     # epoch ms

	•	GCReply:
	•	Para RENOVAR/DEVOLVER: {"id":..., "status":"RECIBIDO"}
	•	Para PRESTAR: {"id":..., "status":"OK"|"ERROR", "reason": Optional[str], "dueDate": Optional[str]}
	•	ActorMessage (GC → AR/AD por PUB):

id: str; sedeId: str; userId: str; libroCodigo: str; op: Literal["RENOVAR","DEVOLVER"]; dueDateNew: Optional[str]

3) Logging JSON estandarizado

common/logging_utils.py
Función json_log(proc, id, op, stage, detail) → imprime una línea JSON:

{ "ts": 1710000000000, "proc": "GC|PS", "id": "uuid", "op": "RENOVAR|DEVOLVER|PRESTAR",
  "stage": "recibido|enviado|aplicado|error", "detail": "texto"}

Usa rich para modo humano (--pretty).

4) GC — server.py (Alejandro)

Implementa dos sockets:
	•	REQ/REP (bind GC_BIND): recibe ClientRequest desde PS y responde GCReply.
	•	PUB (bind GC_PUB_BIND): publica en tópicos TOPIC_RENOVACION y TOPIC_DEVOLUCION los ActorMessage para AR/AD.
	•	REQ a AP (AP_REQ_CONNECT): para PRESTAR, GC hace round-trip con AP y luego responde al PS.

Reglas de enrutamiento (router.py)
	•	RENOVAR:
	1.	Validar payload.
	2.	Responder al PS inmediatamente {"status":"RECIBIDO"}.
	3.	Publicar en tópico RENOVACION el ActorMessage con dueDateNew = now()+7d (formato YYYY-MM-DD).
	•	DEVOLVER: igual, tópico DEVOLUCION, sin dueDateNew.
	•	PRESTAR:
	1.	Encapsular solicitud y enviar REQ a AP_REQ_CONNECT.
	2.	Esperar respuesta {ok, reason?, metadata:{dueDate}}.
	3.	Responder al PS {"status":"OK|ERROR","reason","dueDate"}.

Modos GC (modes.py)
	•	serial: bucle que atiende de a 1 solicitud PS por vez (bloqueante).
	•	threaded: bucle que acepta solicitudes y las delega a un ThreadPoolExecutor (tamaño configurable por --workers), manteniendo orden de respuesta por socket.

CLI GC

python -m gc.server --mode {serial|threaded} --workers 8 --pretty
	•	--mode sobreescribe GC_MODE si se pasa por CLI.
	•	Logs: stage=recibido (PS→GC), stage=enviado (GC→PUB o GC→AP), stage=aplicado (cuando llega respuesta de AP y se responde PS), stage=error en excepciones.

Tolerancia (mock opcional)

Si Sebastián aún no tiene AP listo, agrega flag --mock-ap que responde {"ok": True, "metadata":{"dueDate": today+14}} en local, sin red (útil para tus pruebas y métricas).

5) PS — client.py y workload.py (Alejandro)
	•	client.py:
	•	Conecta a GC_BIND vía REQ.
	•	CLI:

python -m ps.client --sede A --file data/ejemplos/peticiones_sample.txt --pretty


	•	Lee líneas tipo:

PRESTAR ISBN-0001 u-1
RENOVAR ISBN-0100 u-17
DEVOLVER ISBN-0099 u-5


	•	Por cada línea, construye ClientRequest con id=uuid4, timestamp=now_ms(), envía, mide latencia solo para PRESTAR (t_roundtrip), y la retorna al agregador (ver spawn_ps.py).

	•	workload.py:
	•	Genera pausas aleatorias pequeñas (p.ej. 10–50 ms) para simular intercalado.
	•	Valida errores de formato y los ignora con log stage=error.

6) Generador de carga — tools/spawn_ps.py (Alejandro)

CLI:

python tools/spawn_ps.py \
  --ps-per-site 4 \
  --sites A,B \
  --duration-sec 120 \
  --file data/ejemplos/peticiones_sample.txt \
  --gc tcp://{IP_GC}:5555 \
  --mode serial \
  --out metrics/results.csv

Comportamiento:
	•	Lanza N procesos PS por cada sitio (A y B).
	•	Cada PS reporta al proceso padre:
	•	latencias (ms) de cada PRESTAR,
	•	conteo de PRESTAR OK dentro de la ventana,
	•	totales por PS.
	•	Al final, el padre calcula:
	•	avg_ms, stdev_ms de PRESTAR,
	•	count_2min (OKs)
y append a CSV con columnas:

timestamp, ps_per_site, mode, avg_ms, stdev_ms, count_2min

7) Gráficas — tools/charts.py (Alejandro)
	•	Lee metrics/results.csv.
	•	Genera 2 PNG:
	1.	latency_vs_ps.png → eje X = ps_per_site; eje Y = avg_ms; barras de error con stdev.
	2.	throughput_vs_ps.png → eje X = ps_per_site; eje Y = count_2min.
	•	Sin estilos ni colores específicos (defaults). Fondo transparente si es fácil.

CLI:

python tools/charts.py --csv metrics/results.csv --outdir metrics/

8) Demo — tools/demo.sh (Alejandro)

Script bash (Linux/Mac) que:
	1.	Arranca GC en --mode serial (o threaded si se pasa --threaded).
	2.	Ejecuta un PS simple (renovación y devolución) y muestra logs.
	3.	Lanza spawn_ps.py con --ps-per-site 4 por 120s.
	4.	Ejecuta charts.py y deja PNG en metrics/.

Debe imprimir pasos claros y rutas de archivos.

9) Seguridad y robustez mínimas
	•	Validación estricta con Pydantic; rechaza campos faltantes con status="ERROR" (sólo si aplica).
	•	Manejo de timeouts al hablar con AP (configurable, p.ej. 3s).
	•	Reintentos a AP (1 reintento) con backoff leve.
	•	Cierre limpio de sockets (SIGINT/SIGTERM).
	•	Logs siempre con id para trazabilidad.

10) Tests manuales (sin Sebastián)
	•	Arranca GC con --mock-ap.
	•	Ejecuta ps.client con un archivo de 20–30 operaciones mezcladas.
	•	Verifica:
	•	Para RENOVAR/DEVOLVER, respuesta RECIBIDO + publicación en los tópicos (puedes loguear “publicado RENOVACION/DEVOLUCION”).
	•	Para PRESTAR, status=OK y dueDate presente.
	•	Ejecuta spawn_ps.py 120s y valida que se cree/actualice metrics/results.csv; genera gráficos.

11) Compatibilidad con Sebastián (actores + GA)
	•	No cambies: TOPIC_RENOVACION, TOPIC_DEVOLUCION.
	•	El ActorMessage debe tener op = RENOVAR o DEVOLVER y dueDateNew solo en RENOVAR.
	•	Para PRESTAR, GC habla con AP por AP_REQ_CONNECT y reenvía la respuesta al PS sin alterar las claves (ok, reason, metadata.dueDate → mapea a dueDate en tu reply).
	•	Todo aquello que dependa de IPs/puertos reales debe salir de .env o CLI.

12) Calidad y DX
	•	requirements.txt con todas las libs.
	•	README.md con:
	•	Cómo crear venv, instalar deps, configurar .env.
	•	Comandos para correr GC, PS, carga y charts.
	•	Ejemplo de peticiones_sample.txt.
	•	Mensajes de ayuda (--help) con typer.

13) Entregables esperados de esta tarea
	•	Código completo en las rutas indicadas.
	•	.env.example listo.
	•	data/ejemplos/peticiones_sample.txt con ≥20 operaciones mezcladas.
	•	metrics/results.csv generado por una corrida de ejemplo.
	•	metrics/latency_vs_ps.png y metrics/throughput_vs_ps.png.
	•	tools/demo.sh funcional.
	•	Logs demostrando:
	•	GC recibe y publica renovaciones y devoluciones (para que AR/AD los vean),
	•	y que para préstamos hace round-trip con AP (cuando Sebastián lo conecte).

Importante: No cambies el contrato. Cualquier detalle que falte, pregúntame con un TODO visible en el código, pero mantén los nombres de claves y los sockets definidos.
