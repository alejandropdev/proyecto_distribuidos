#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Carga (GC) - Sistema Distribuido de Préstamo de Libros
Maneja las solicitudes de renovación, devolución y préstamo usando ZeroMQ REQ/REP y PUB/SUB
"""

import zmq
import json
import threading
import time
import os
import queue
from datetime import datetime, timedelta
import logging
from utils_failover import FailoverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GC - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GestorCarga:
    """
    Gestor de Carga (GC) - Coordina las solicitudes del sistema
    
    El GC actúa como punto central de entrada para todas las solicitudes del sistema.
    Soporta dos modos de operación:
    - Serial: Procesa solicitudes una a la vez en un solo thread
    - Multithread: Procesa múltiples solicitudes concurrentemente usando workers
    
    Patrones de comunicación:
    - REQ/REP (síncrono): Recibe solicitudes de PS, envía préstamos a Actor Préstamo
    - PUB/SUB (asíncrono): Publica eventos de devolución y renovación a actores
    """
    def __init__(self):
        """
        Inicializa el Gestor de Carga
        
        Lee configuración desde variables de entorno:
        - GC_MODE: 'serial' o 'multithread' (default: 'serial')
        - GC_WORKERS: Número de workers en modo multithread (default: 4)
        - GC_HOST, GC_REP_PORT, GC_PUB_PORT: Configuración de sockets
        - ACTOR_PRESTAMO_HOST, ACTOR_PRESTAMO_PORT: Configuración de Actor Préstamo
        - GA_HOST, GA_PORT: Configuración de Gestor de Almacenamiento
        """
        self.context = zmq.Context()
        self.rep_socket = None  # Socket REP para recibir de PS
        self.pub_socket = None  # Socket PUB para enviar eventos a actores
        self.req_actor_prestamo = None  # Socket REQ para comunicarse con actor_prestamo (solo modo serial)
        self.contador_operaciones = 0
        self.contador_lock = threading.Lock()  # Lock para contador thread-safe
        self.running = True
        
        # Leer variables de entorno
        self.gc_host = os.getenv('GC_HOST', '0.0.0.0')
        self.gc_rep_port = int(os.getenv('GC_REP_PORT', '5001'))
        self.gc_pub_port = int(os.getenv('GC_PUB_PORT', '5002'))
        self.actor_prestamo_host = os.getenv('ACTOR_PRESTAMO_HOST', 'actor_prestamo')
        self.actor_prestamo_port = int(os.getenv('ACTOR_PRESTAMO_PORT', '5004'))
        self.ga_host = os.getenv('GA_HOST', 'ga')
        self.ga_port = int(os.getenv('GA_PORT', '5003'))
        
        # Leer modo de operación y número de workers
        gc_mode = os.getenv('GC_MODE', 'serial').lower()
        if gc_mode not in ['serial', 'multithread']:
            logger.warning(f"Modo inválido '{gc_mode}', usando 'serial' por defecto")
            gc_mode = 'serial'
        self.modo = gc_mode
        self.num_workers = int(os.getenv('GC_WORKERS', '4'))
        
        if self.modo == 'multithread':
            logger.info(f"Modo multithread activado con {self.num_workers} workers")
            # Colas para comunicación thread-safe entre main thread y workers
            self.request_queue = queue.Queue()
            self.response_queue = queue.Queue()
            self.workers = []  # Lista de threads workers
        else:
            logger.info("Modo serial activado (comportamiento original)")
        
        # Inicializar failover manager para health checks a GA
        self.failover_manager = FailoverManager(
            ga_host=self.ga_host,
            ga_port=self.ga_port,
            timeout=5,
            retry_interval=30
        )
        
        # Thread para health checks periódicos
        self.health_check_thread = None
        self.health_check_running = True
        
    def inicializar_sockets(self):
        """Inicializa los sockets REQ/REP, PUB/SUB y REQ para actor_prestamo"""
        try:
            # Socket REP para recibir solicitudes del Proceso Solicitante
            self.rep_socket = self.context.socket(zmq.REP)
            bind_address = f"tcp://{self.gc_host}:{self.gc_rep_port}"
            self.rep_socket.bind(bind_address)
            logger.info(f"Socket REP inicializado en {bind_address}")
            
            # Socket PUB para enviar eventos a los actores (devolución y renovación)
            # Compartido entre threads en modo multithread (thread-safe en ZeroMQ)
            self.pub_socket = self.context.socket(zmq.PUB)
            bind_address_pub = f"tcp://{self.gc_host}:{self.gc_pub_port}"
            self.pub_socket.bind(bind_address_pub)
            logger.info(f"Socket PUB inicializado en {bind_address_pub}")
            
            # Socket REQ para comunicarse con actor_prestamo
            # Solo en modo serial; en modo multithread cada worker tiene su propio socket
            if self.modo == 'serial':
                self.req_actor_prestamo = self.context.socket(zmq.REQ)
                self.req_actor_prestamo.setsockopt(zmq.RCVTIMEO, 10000)  # 10 segundos timeout
                actor_address = f"tcp://{self.actor_prestamo_host}:{self.actor_prestamo_port}"
                self.req_actor_prestamo.connect(actor_address)
                logger.info(f"Socket REQ conectado a Actor Préstamo en {actor_address}")
            
            # Pequeña pausa para asegurar que los sockets estén listos
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error inicializando sockets: {e}")
            raise
    
    def procesar_solicitud(self, mensaje_json, req_socket=None):
        """Procesa una solicitud y genera el evento correspondiente o reenvía a actor_prestamo
        
        Args:
            mensaje_json: Mensaje JSON con la solicitud
            req_socket: Socket REQ a usar para préstamos (None para modo serial)
        """
        try:
            datos = json.loads(mensaje_json)
            operacion = datos.get('op', '').upper()
            libro_id = datos.get('libro_id', '')
            usuario_id = datos.get('usuario_id', '')
            sede = datos.get('sede', 'SEDE_1')
            search_criteria = datos.get('search_criteria')
            
            # Procesar PRESTAMO de forma síncrona vía REQ/REP con actor_prestamo
            if operacion == 'PRESTAMO':
                return self.procesar_prestamo(datos, req_socket=req_socket)
            
            # Procesar RENOVACION y DEVOLUCION de forma asíncrona vía PUB/SUB
            elif operacion in ['RENOVACION', 'DEVOLUCION']:
                return self.procesar_operacion_asincrona(operacion, libro_id, usuario_id, sede)
            
            else:
                return {
                    "status": "ERROR",
                    "message": f"Operación inválida: {operacion}. Solo se permiten PRESTAMO, RENOVACION y DEVOLUCION"
                }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            return {
                "status": "ERROR",
                "message": "Formato JSON inválido"
            }
        except Exception as e:
            logger.error(f"Error procesando solicitud: {e}")
            return {
                "status": "ERROR",
                "message": f"Error interno: {str(e)}"
            }
    
    def procesar_prestamo(self, datos, req_socket=None):
        """Procesa una solicitud de préstamo reenviándola a actor_prestamo
        
        Args:
            datos: Datos de la solicitud
            req_socket: Socket REQ a usar (None para usar self.req_actor_prestamo en modo serial)
        """
        try:
            # Usar socket proporcionado o el socket compartido (modo serial)
            socket_a_usar = req_socket if req_socket is not None else self.req_actor_prestamo
            
            # Crear solicitud para actor_prestamo
            solicitud_prestamo = {
                "operacion": "PRESTAMO",
                "libro_id": datos.get('libro_id'),
                "usuario_id": datos.get('usuario_id'),
                "sede": datos.get('sede', 'SEDE_1'),
                "search_criteria": datos.get('search_criteria')
            }
            
            solicitud_json = json.dumps(solicitud_prestamo, ensure_ascii=False)
            
            logger.info(f"Reenviando préstamo a Actor Préstamo: {solicitud_json}")
            
            # Enviar a actor_prestamo
            socket_a_usar.send(solicitud_json.encode('utf-8'))
            
            # Recibir respuesta
            respuesta_bytes = socket_a_usar.recv()
            respuesta_str = respuesta_bytes.decode('utf-8')
            respuesta = json.loads(respuesta_str)
            
            # Incrementar contador de forma thread-safe
            with self.contador_lock:
                self.contador_operaciones += 1
                contador_actual = self.contador_operaciones
            
            if respuesta.get('success'):
                logger.info(f"Préstamo #{contador_actual} exitoso: {respuesta.get('message')}")
                return {
                    "status": "OK",
                    "message": respuesta.get('message'),
                    "operacion": "PRESTAMO",
                    "libro_id": respuesta.get('libro_id'),
                    "ejemplar_id": respuesta.get('ejemplar_id'),
                    "fecha_devolucion": respuesta.get('fecha_devolucion')
                }
            else:
                logger.error(f"Préstamo #{contador_actual} falló: {respuesta.get('message')}")
                return {
                    "status": "ERROR",
                    "message": respuesta.get('message'),
                    "operacion": "PRESTAMO"
                }
        
        except zmq.Again:
            logger.error("Timeout esperando respuesta de Actor Préstamo")
            return {
                "status": "ERROR",
                "message": "Timeout: Actor Préstamo no respondió"
            }
        except Exception as e:
            logger.error(f"Error procesando préstamo: {e}")
            return {
                "status": "ERROR",
                "message": f"Error comunicándose con Actor Préstamo: {str(e)}"
            }
    
    def procesar_operacion_asincrona(self, operacion, libro_id, usuario_id, sede):
        """Procesa operaciones asíncronas (RENOVACION, DEVOLUCION)"""
        # Crear evento con timestamp
        timestamp = datetime.utcnow().isoformat()
        evento = {
            "operacion": operacion,
            "libro_id": libro_id,
            "usuario_id": usuario_id,
            "sede": sede,
            "timestamp": timestamp
        }
        
        # Para renovación, calcular nueva fecha de devolución (+7 días)
        if operacion == 'RENOVACION':
            nueva_fecha = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            evento["nueva_fecha_devolucion"] = nueva_fecha
        
        # Enviar evento a los actores correspondientes
        self.enviar_evento_a_actores(evento)
        
        # Incrementar contador de forma thread-safe
        with self.contador_lock:
            self.contador_operaciones += 1
            contador_actual = self.contador_operaciones
        
        logger.info(f"Operación #{contador_actual} procesada: {operacion} - Libro {libro_id} - Usuario {usuario_id}")
        
        return {
            "status": "OK",
            "message": "Recibido. Procesando...",
            "operacion": operacion,
            "libro_id": libro_id
        }
    
    def enviar_evento_a_actores(self, evento):
        """Envía el evento a los actores correspondientes vía PUB/SUB"""
        try:
            operacion = evento['operacion']
            topic = operacion.lower()  # 'renovacion' o 'devolucion'
            
            # Serializar evento como JSON
            mensaje_evento = json.dumps(evento, ensure_ascii=False)
            
            # Enviar con el topic correspondiente
            self.pub_socket.send_multipart([topic.encode('utf-8'), mensaje_evento.encode('utf-8')])
            
            logger.info(f"Evento enviado a actores - Topic: {topic} - Evento: {evento}")
            
        except Exception as e:
            logger.error(f"Error enviando evento a actores: {e}")
    
    def _worker_loop(self, worker_id, req_socket):
        """
        Loop de trabajo para un worker thread en modo multithread
        
        Cada worker:
        1. Obtiene solicitudes de la cola de requests
        2. Procesa la solicitud (puede ser préstamo, devolución o renovación)
        3. Envía la respuesta a la cola de respuestas
        
        El worker mantiene su propio socket REQ hacia Actor Préstamo para
        permitir procesamiento concurrente de préstamos.
        
        Args:
            worker_id: ID único del worker (para logging)
            req_socket: Socket REQ propio del worker para comunicarse con actor_prestamo
        """
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.running:
            try:
                # Obtener solicitud de la cola (con timeout para poder verificar self.running)
                try:
                    request_data = self.request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                mensaje_str, request_id = request_data
                
                logger.info(f"Worker {worker_id} procesando solicitud {request_id}: {mensaje_str}")
                
                # Procesar solicitud (pasar req_socket para préstamos)
                respuesta = self.procesar_solicitud(mensaje_str, req_socket=req_socket)
                
                # Enviar respuesta a la cola de respuestas
                respuesta_json = json.dumps(respuesta, ensure_ascii=False)
                self.response_queue.put((request_id, respuesta_json))
                
                logger.info(f"Worker {worker_id} completó solicitud {request_id}")
                
            except Exception as e:
                logger.error(f"Error en worker {worker_id}: {e}")
        
        # Cerrar socket del worker
        if req_socket:
            req_socket.close()
        logger.info(f"Worker {worker_id} detenido")
    
    def _iniciar_workers(self):
        """
        Inicia los worker threads en modo multithread
        
        Crea N workers (donde N = self.num_workers), cada uno con:
        - Su propio socket REQ hacia Actor Préstamo
        - Acceso a las colas thread-safe (request_queue, response_queue)
        - Acceso compartido al socket PUB (thread-safe en ZeroMQ)
        
        Los workers se ejecutan como threads daemon y procesan solicitudes
        de forma concurrente mientras se mantiene la semántica REQ/REP.
        """
        logger.info(f"Iniciando {self.num_workers} workers...")
        
        for i in range(self.num_workers):
            # Cada worker tiene su propio socket REQ para actor_prestamo
            req_socket = self.context.socket(zmq.REQ)
            req_socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 segundos timeout
            actor_address = f"tcp://{self.actor_prestamo_host}:{self.actor_prestamo_port}"
            req_socket.connect(actor_address)
            
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i + 1, req_socket),
                daemon=True
            )
            worker.start()
            self.workers.append((worker, req_socket))
            logger.info(f"Worker {i + 1} iniciado con socket REQ conectado a {actor_address}")
        
        # Pequeña pausa para asegurar que los workers estén listos
        time.sleep(0.5)
        logger.info(f"Todos los {self.num_workers} workers iniciados")
    
    def manejar_solicitudes(self):
        """Maneja las solicitudes entrantes del Proceso Solicitante"""
        logger.info(f"Iniciando manejo de solicitudes en modo {self.modo}...")
        
        if self.modo == 'multithread':
            # Iniciar workers
            self._iniciar_workers()
            
            # Contador para IDs de solicitudes
            request_counter = 0
            # Diccionario para mapear request_id -> respuesta (para manejar respuestas fuera de orden)
            pending_responses = {}
            
            while self.running:
                try:
                    # Recibir solicitud (bloqueante - REP socket requiere request-response pairing)
                    mensaje = self.rep_socket.recv()
                    mensaje_str = mensaje.decode('utf-8')
                    request_counter += 1
                    request_id = request_counter
                    
                    logger.info(f"Solicitud recibida (ID: {request_id}): {mensaje_str}")
                    
                    # Enviar a la cola de requests para procesamiento por worker
                    self.request_queue.put((mensaje_str, request_id))
                    
                    # Esperar respuesta del worker, verificando si ya llegó (puede haber llegado antes)
                    respuesta_json = None
                    while respuesta_json is None:
                        # Verificar si la respuesta ya está disponible
                        if request_id in pending_responses:
                            respuesta_json = pending_responses.pop(request_id)
                            break
                        
                        # Intentar obtener respuesta de la cola (con timeout corto)
                        try:
                            request_id_resp, respuesta_json_temp = self.response_queue.get(timeout=0.1)
                            if request_id_resp == request_id:
                                # Esta es la respuesta que esperamos
                                respuesta_json = respuesta_json_temp
                                break
                            else:
                                # Esta es una respuesta para otra solicitud, guardarla
                                pending_responses[request_id_resp] = respuesta_json_temp
                        except queue.Empty:
                            # Continuar esperando
                            continue
                    
                    # Enviar respuesta de vuelta al cliente (REP socket requiere respuesta antes del siguiente recv)
                    self.rep_socket.send(respuesta_json.encode('utf-8'))
                    logger.info(f"Respuesta enviada (ID: {request_id}): {respuesta_json}")
                    
                except Exception as e:
                    logger.error(f"Error manejando solicitudes: {e}")
                    time.sleep(1)
        else:
            # Modo serial: comportamiento original
            while self.running:
                try:
                    # Recibir solicitud del Proceso Solicitante
                    mensaje = self.rep_socket.recv(zmq.NOBLOCK)
                    mensaje_str = mensaje.decode('utf-8')
                    
                    logger.info(f"Solicitud recibida: {mensaje_str}")
                    
                    # Procesar solicitud
                    respuesta = self.procesar_solicitud(mensaje_str)
                    
                    # Enviar respuesta inmediata (REQ/REP pattern)
                    respuesta_json = json.dumps(respuesta, ensure_ascii=False)
                    self.rep_socket.send(respuesta_json.encode('utf-8'))
                    
                    logger.info(f"Respuesta enviada: {respuesta_json}")
                    
                except zmq.Again:
                    # No hay mensajes disponibles, continuar
                    time.sleep(0.1)
                    continue
                except Exception as e:
                    logger.error(f"Error manejando solicitudes: {e}")
                    time.sleep(1)
    
    def health_check_loop(self):
        """Loop de health checks periódicos a GA"""
        while self.health_check_running:
            try:
                resultado = self.failover_manager.health_check()
                if resultado.get('ok'):
                    logger.debug(f"Health check GA: {resultado.get('status')}")
                else:
                    logger.warning(f"Health check GA falló: {resultado.get('message')}")
            except Exception as e:
                logger.error(f"Error en health check: {e}")
            
            time.sleep(30)  # Health check cada 30 segundos
    
    def iniciar(self):
        """Inicia el Gestor de Carga"""
        try:
            logger.info("Iniciando Gestor de Carga...")
            self.inicializar_sockets()
            
            # Iniciar thread de health checks
            self.health_check_thread = threading.Thread(target=self.health_check_loop, daemon=True)
            self.health_check_thread.start()
            
            logger.info("Gestor de Carga iniciado correctamente")
            logger.info(f"Modo de operación: {self.modo.upper()}")
            if self.modo == 'multithread':
                logger.info(f"Número de workers: {self.num_workers}")
            logger.info(f"Esperando solicitudes en puerto {self.gc_rep_port}...")
            logger.info(f"Listo para publicar eventos en puerto {self.gc_pub_port}...")
            if self.modo == 'serial':
                logger.info(f"Conectado a Actor Préstamo en {self.actor_prestamo_host}:{self.actor_prestamo_port}")
            logger.info(f"Monitoreando GA en {self.ga_host}:{self.ga_port}")
            
            # Iniciar manejo de solicitudes
            self.manejar_solicitudes()
            
        except KeyboardInterrupt:
            logger.info("Deteniendo Gestor de Carga...")
            self.detener()
        except Exception as e:
            logger.error(f"Error fatal en Gestor de Carga: {e}")
            self.detener()
    
    def detener(self):
        """Detiene el Gestor de Carga"""
        self.running = False
        self.health_check_running = False
        
        # Esperar a que los workers terminen (en modo multithread)
        if self.modo == 'multithread' and self.workers:
            logger.info("Esperando a que los workers terminen...")
            for worker, req_socket in self.workers:
                worker.join(timeout=2.0)
                if req_socket:
                    req_socket.close()
            logger.info("Todos los workers detenidos")
        
        if self.failover_manager:
            self.failover_manager.cerrar()
        
        if self.req_actor_prestamo:
            self.req_actor_prestamo.close()
        if self.rep_socket:
            self.rep_socket.close()
        if self.pub_socket:
            self.pub_socket.close()
        if self.context:
            self.context.term()
        
        logger.info(f"Total de operaciones procesadas: {self.contador_operaciones}")
        logger.info("Gestor de Carga detenido")

def main():
    """Función principal"""
    gc = GestorCarga()
    gc.iniciar()

if __name__ == "__main__":
    main()
