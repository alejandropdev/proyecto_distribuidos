📘 Proyecto — Primera Entrega

Sistema Distribuido de Préstamo de Libros (40%)
Entrega 1: 15% del total — Semana 10

⸻

🎯 Objetivo de la primera entrega

Diseñar e implementar la versión inicial funcional del sistema distribuido de préstamo de libros, enfocándose en las operaciones devolución y renovación, con comunicación entre procesos distribuidos en al menos dos computadoras.

⸻

🧩 Funcionalidades mínimas a mostrar

1. Operaciones implementadas
	•	Renovación de libros
	•	Se realiza por una semana adicional.
	•	Máximo dos renovaciones por libro.
	•	La operación se responde de inmediato al cliente (PS).
	•	Luego se publica en el tópico RENOVACION para que el ActorRenovación actualice la base de datos.
	•	Devolución de libros
	•	El GC acepta y responde inmediatamente al PS.
	•	Luego publica en el tópico DEVOLUCION para que el ActorDevolución actualice la base de datos.

Ambas operaciones deben mostrar mensajes en consola (o logs) que evidencien el flujo de comunicación:
PS → GC → Actor → GA.

Se debe observar claramente que:
	•	El GC recibe y enruta los mensajes.
	•	El Actor correspondiente procesa la operación.
	•	El GA actualiza la base de datos.

⸻

2. Comunicación distribuida
	•	Usar ZeroMQ obligatoriamente.
	•	Patrones requeridos:
	•	PS ⇄ GC: Request / Reply (REQ / REP)
	•	GC → Actores (Renovación, Devolución): Publisher / Subscriber (PUB / SUB)
	•	Actores ⇄ GA: Request / Reply (REQ / REP)

Las operaciones de préstamo no son obligatorias en esta entrega (solo renovación y devolución).

⸻

3. Mecanismo de generación de carga

Debe existir una forma de generar múltiples solicitudes automáticamente:
	•	Opción A: lectura desde un archivo de texto (peticiones.txt) con al menos 20 requerimientos de los tres tipos.
	•	Opción B: uso de un generador de carga externo (JMETER o Locust).

Cada proceso solicitante (PS) debe recibir como argumento el archivo con sus solicitudes.

⸻

4. Distribución en máquinas

El sistema debe ejecutarse en al menos dos computadoras físicas o virtuales:

Computador	Contiene
1	Gestor de Carga (GC) + Actores (Renovación, Devolución)
2	Procesos Solicitantes (PS)

La comunicación entre ambas máquinas debe funcionar mediante ZeroMQ con direcciones IP reales o locales.

⸻

5. Datos iniciales
	•	Base de datos inicial (archivo o BD real) con al menos 1000 libros, de los cuales 200 ya están prestados.
	•	Campos mínimos: codigo, titulo, disponible (booleano o cantidad).
	•	Ambas sedes deben tener una copia idéntica de la base de datos al inicio.

⸻

6. Pruebas y visualización
	•	Mostrar durante la sustentación:
	1.	Estado inicial de la BD (original y réplica).
	2.	Operaciones ejecutadas por cada proceso (PS, GC, Actor, GA).
	3.	Resultado final de las operaciones.

El objetivo es evidenciar que los mensajes fluyen correctamente y que la BD se actualiza en el GA.

⸻

🧾 Informe requerido

Debe incluir:
	1.	Modelos del sistema:
	•	Modelo arquitectónico (cómo se comunican los procesos).
	•	Modelo de interacción.
	•	Modelo de fallas.
	•	Modelo de seguridad.
	2.	Diseño del sistema:
	•	Diagrama de despliegue
	•	Diagrama de componentes
	•	Diagrama de clases
	•	Diagrama de secuencia
(incluyendo los componentes que manejan fallas o replicación)
	3.	Protocolo de pruebas:
	•	Tipos de pruebas planeadas (funcionalidad, fallas, rendimiento).
	•	Cómo se evaluará la latencia, tiempos de respuesta, etc.
	4.	Obtención de métricas de desempeño:
	•	Describir cómo se van a medir las métricas (instrumentación interna o herramientas externas).
	•	Si se usan herramientas externas, especificar cuáles y cómo.

⸻

🧩 Requisitos técnicos mínimos
	•	Uso de ZeroMQ en todos los canales de comunicación.
	•	Implementación modular y distribuida (mínimo 2 computadores).
	•	Lectura automática de peticiones.
	•	Logs o mensajes que permitan visualizar la secuencia completa de cada operación.
	•	BD persistente o archivos JSON simulando persistencia.

⸻

🕒 Sustentación
	•	Cada grupo tiene 15 minutos.
	•	Mostrar primero las funcionalidades en ejecución (renovación y devolución).
	•	Luego, los diagramas y la estructura del sistema.
	•	Responder preguntas sobre fallas, comunicación y desempeño.

⸻

🧮 Criterios de evaluación (5 puntos totales)

Criterio	Peso	Excelente	Competente	Deficiente
Informe (presentación, redacción, completitud)	0.5	Impecable, completo	Fallas menores	Incompleto o mal redactado
Diseño del sistema	1.5	Todos los diagramas correctos	Incompletos o con errores	No presentados o incorrectos
Protocolo de pruebas	0.5	Pruebas suficientes (fallas y rendimiento)	Incompleto	No presentado
Modelos del sistema (interacción, fallas, seguridad)	0.25	Claros y adaptados al proyecto	Parciales	No relacionados o ausentes
Obtención de métricas de rendimiento	0.25	Claramente descrito	Poco claro	No descrito
Implementación inicial (funcionamiento)	2	Funcional en 2 máquinas, operaciones correctas	Fallas parciales	Deficiente o no ejecuta
TOTAL	5 pts	—	—	—


⸻

✅ Resumen de alcance para Cursor

Para la primera entrega, el sistema debe:
	•	Tener PS, GC, Actores (Renovación y Devolución) y GA.
	•	Usar ZeroMQ (REQ/REP y PUB/SUB).
	•	Leer peticiones desde archivo.
	•	Actualizar la base de datos con GA.
	•	Mostrar logs claros.
	•	Ejecutarse en 2 máquinas.
	•	Entregar diagramas, modelos, protocolo y descripción de métricas.
