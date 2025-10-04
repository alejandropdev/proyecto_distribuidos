You are an expert backend and distributed systems engineer.  
Create a **complete Python project** that fulfills the **Entrega #1** requirements from the “Sistema Distribuido de Préstamo de Libros” document (Pontificia Universidad Javeriana).

The project must run entirely in **Docker containers**, each representing an independent computer on a private Docker network, and must demonstrate a truly distributed system with multiple processes communicating via **ZeroMQ** sockets.

──────────────────────────────
🎯 OBJECTIVE (Entrega #1)
──────────────────────────────
Implement a working distributed system that supports the operations:
- **RENOVACIÓN** (Renewal)
- **DEVOLUCIÓN** (Return)

The system must:
1. Include at least 3 processes distributed in a minimum of 2 “computers” (→ we’ll simulate with Docker containers and unique IPs).
2. Use **ZeroMQ** communication patterns:
   - **REQ/REP** → between the *Proceso Solicitante (PS)* and *Gestor de Carga (GC)*.
   - **PUB/SUB** → between *GC* and *Actores (Renovación, Devolución)*.
3. Send and receive messages over TCP sockets (no shared memory).
4. Allow sending operations from files (“archivos de carga”) with mixed requests.
5. Respond immediately from the GC to the PS (synchronous ACK) and then propagate events asynchronously to the actors (simulating the asynchronous layer).
6. Log all messages and events with timestamps.
7. Be fully runnable with `docker compose up`.

──────────────────────────────
🧱 PROJECT STRUCTURE
──────────────────────────────

sistema_distribuido/
│
├── gestor_carga.py          # Central load manager
├── proceso_solicitante.py   # Client that sends renewal/return requests
├── actor_devolucion.py      # Subscriber to ‘devolucion’ topic
├── actor_renovacion.py      # Subscriber to ‘renovacion’ topic
│
├── data/
│   ├── libros.json          # Mock DB
│   └── solicitudes.txt      # List of requests
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml

──────────────────────────────
⚙️ GENERAL BEHAVIOR
──────────────────────────────

1. **Gestor de Carga (GC)**
   - Binds a **REP** socket at `tcp://0.0.0.0:5001` to receive requests from PS.
   - Binds a **PUB** socket at `tcp://0.0.0.0:5002` to broadcast events to the actors.
   - For every received request:
     - Parse JSON `{ "op": "RENOVACION" | "DEVOLUCION", "libro_id": "L001", "usuario_id": "U001", "sede": "SEDE_1" }`
     - Immediately reply `{ "status": "OK", "message": "Recibido. Procesando..." }` (REQ/REP pattern).
     - Create an **event** with timestamp and, for RENOVACIÓN, a new return date (+7 days).
     - Publish it asynchronously with the topic “renovacion” or “devolucion”.
   - Handle malformed JSON safely and never crash.
   - Log all requests and events to console with timestamps.

2. **Proceso Solicitante (PS)**
   - Connects to GC using `tcp://gc:5001` (Docker resolves `gc` as hostname).
   - Reads from `data/solicitudes.txt`, line by line (e.g., `DEVOLUCION L002 U005`, `RENOVACION L001 U003`).
   - For each line:
     - Parse operation, build JSON request, send via REQ socket.
     - Print GC response to console.
     - Wait 1 second between requests (simulate real workload).

3. **Actor de Devolución**
   - Connects to GC’s PUB socket (`tcp://gc:5002`) as SUB.
   - Subscribes to topic “devolucion”.
   - Upon receiving an event:
     - Update `data/libros.json`: increase `"ejemplares_disponibles"` of the book by 1.
     - Log “Libro LXXX devuelto por usuario UYYY”.
     - Save JSON file.

4. **Actor de Renovación**
   - Connects to GC’s PUB socket (`tcp://gc:5002`) as SUB.
   - Subscribes to topic “renovacion”.
   - Upon receiving an event:
     - Update `"fecha_devolucion"` of that book to the new date.
     - Log “Libro LXXX renovado por usuario UYYY hasta FECHA”.
     - Save JSON file.

──────────────────────────────
📁 DATA FILES
──────────────────────────────

`data/libros.json`
```json
[
  {"libro_id": "L001", "titulo": "1984", "ejemplares_disponibles": 2, "fecha_devolucion": "2025-10-01"},
  {"libro_id": "L002", "titulo": "El Principito", "ejemplares_disponibles": 1, "fecha_devolucion": "2025-10-02"},
  {"libro_id": "L003", "titulo": "Cien Años de Soledad", "ejemplares_disponibles": 0, "fecha_devolucion": "2025-09-30"}
]

data/solicitudes.txt

RENOVACION L001 U001
DEVOLUCION L002 U002
RENOVACION L003 U003
DEVOLUCION L001 U004
RENOVACION L002 U005
DEVOLUCION L003 U006

──────────────────────────────
🔌 DOCKER CONFIGURATION
──────────────────────────────

Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

requirements.txt

pyzmq
python-dateutil

docker-compose.yml

version: '3.8'

services:
  gc:
    build: .
    container_name: gc
    command: python gestor_carga.py
    ports:
      - "5001:5001"
      - "5002:5002"

  actor_devolucion:
    build: .
    container_name: actor_dev
    command: python actor_devolucion.py
    depends_on:
      - gc

  actor_renovacion:
    build: .
    container_name: actor_ren
    command: python actor_renovacion.py
    depends_on:
      - gc

  ps:
    build: .
    container_name: ps
    command: python proceso_solicitante.py
    depends_on:
      - gc

networks:
  default:
    name: red_distribuida

──────────────────────────────
💻 EXECUTION INSTRUCTIONS
──────────────────────────────
	1.	Run: docker compose up --build
	2.	The containers will launch in order:
	•	gc → central load manager
	•	actor_dev → subscriber to devolucion
	•	actor_ren → subscriber to renovacion
	•	ps → client sending operations
	3.	Observe console logs:
	•	PS sending JSON requests and GC replying.
	•	GC publishing async messages.
	•	Both actors updating data/libros.json.

──────────────────────────────
🧮 METRICS & TEST LOGGING
──────────────────────────────
	•	Each service prints timestamps and events.
	•	Add message counters inside GC and PS to log how many operations were processed successfully.
	•	Include artificial delay (1 second in PS) to simulate real workload.
	•	All logs must clearly show message flow between containers.

──────────────────────────────
🧱 TECHNICAL DETAILS TO IMPLEMENT
──────────────────────────────
	•	All communication via TCP sockets, not localhost-only.
	•	Each service runs indefinitely unless stopped (Ctrl+C).
	•	JSON messages must be fully serializable.
	•	Use simple print() logs for traceability.
	•	Use UTC timestamps (datetime.utcnow().isoformat()).
	•	GC must handle invalid operations gracefully and respond { "status": "ERROR", "message": "Invalid operation" }.

──────────────────────────────
🧩 FINAL GOAL
──────────────────────────────
Deliver a working distributed system with:
	•	Four containers (each with its own IP).
	•	Real ZeroMQ communication.
	•	RENOVACIÓN and DEVOLUCIÓN flows working end-to-end.
	•	Logs showing message exchange between processes.

──────────────────────────────
📄 BONUS: DOCUMENTATION NOTES (optional but recommended)
──────────────────────────────
Generate Markdown files (optional) to describe:
	•	docs/arquitectura.md → deployment diagram (containers + ports)
	•	docs/interaccion.md → sequence of messages for a RENOVACIÓN
	•	docs/metricas.md → how to measure latency or number of processed messages
	•	docs/fallos_y_seguridad.md → what happens if an actor is offline (retry when reconnects)

---

## ✅ Qué obtendrás con este prompt
- Código **completo y funcional** (4 scripts + Docker + datos).
- Sistema **100% distribuido** (4 contenedores con IPs distintas).
- Cumple todos los puntos de la **Entrega #1** del enunciado (estructura, comunicación, logs, métricas, pruebas, diseño distribuido).
- Listo para correr con **un solo comando** (`docker compose up --build`).
