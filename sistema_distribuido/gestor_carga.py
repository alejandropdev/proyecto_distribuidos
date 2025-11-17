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
    def __init__(self):
        self.context = zmq.Context()
        self.rep_socket = None  # Socket REP para recibir de PS
        self.pub_socket = None  # Socket PUB para enviar eventos a actores
        self.req_actor_prestamo = None  # Socket REQ para comunicarse con actor_prestamo
        self.contador_operaciones = 0
        self.running = True
        
        # Leer variables de entorno
        self.gc_host = os.getenv('GC_HOST', '0.0.0.0')
        self.gc_rep_port = int(os.getenv('GC_REP_PORT', '5001'))
        self.gc_pub_port = int(os.getenv('GC_PUB_PORT', '5002'))
        self.actor_prestamo_host = os.getenv('ACTOR_PRESTAMO_HOST', 'actor_prestamo')
        self.actor_prestamo_port = int(os.getenv('ACTOR_PRESTAMO_PORT', '5004'))
        self.ga_host = os.getenv('GA_HOST', 'ga')
        self.ga_port = int(os.getenv('GA_PORT', '5003'))
        
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
            self.pub_socket = self.context.socket(zmq.PUB)
            bind_address_pub = f"tcp://{self.gc_host}:{self.gc_pub_port}"
            self.pub_socket.bind(bind_address_pub)
            logger.info(f"Socket PUB inicializado en {bind_address_pub}")
            
            # Socket REQ para comunicarse con actor_prestamo
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
    
    def procesar_solicitud(self, mensaje_json):
        """Procesa una solicitud y genera el evento correspondiente o reenvía a actor_prestamo"""
        try:
            datos = json.loads(mensaje_json)
            operacion = datos.get('op', '').upper()
            libro_id = datos.get('libro_id', '')
            usuario_id = datos.get('usuario_id', '')
            sede = datos.get('sede', 'SEDE_1')
            search_criteria = datos.get('search_criteria')
            
            # Procesar PRESTAMO de forma síncrona vía REQ/REP con actor_prestamo
            if operacion == 'PRESTAMO':
                return self.procesar_prestamo(datos)
            
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
    
    def procesar_prestamo(self, datos):
        """Procesa una solicitud de préstamo reenviándola a actor_prestamo"""
        try:
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
            self.req_actor_prestamo.send(solicitud_json.encode('utf-8'))
            
            # Recibir respuesta
            respuesta_bytes = self.req_actor_prestamo.recv()
            respuesta_str = respuesta_bytes.decode('utf-8')
            respuesta = json.loads(respuesta_str)
            
            self.contador_operaciones += 1
            
            if respuesta.get('success'):
                logger.info(f"Préstamo #{self.contador_operaciones} exitoso: {respuesta.get('message')}")
                return {
                    "status": "OK",
                    "message": respuesta.get('message'),
                    "operacion": "PRESTAMO",
                    "libro_id": respuesta.get('libro_id'),
                    "ejemplar_id": respuesta.get('ejemplar_id'),
                    "fecha_devolucion": respuesta.get('fecha_devolucion')
                }
            else:
                logger.error(f"Préstamo #{self.contador_operaciones} falló: {respuesta.get('message')}")
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
        
        self.contador_operaciones += 1
        logger.info(f"Operación #{self.contador_operaciones} procesada: {operacion} - Libro {libro_id} - Usuario {usuario_id}")
        
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
    
    def manejar_solicitudes(self):
        """Maneja las solicitudes entrantes del Proceso Solicitante"""
        logger.info("Iniciando manejo de solicitudes...")
        
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
            logger.info(f"Esperando solicitudes en puerto {self.gc_rep_port}...")
            logger.info(f"Listo para publicar eventos en puerto {self.gc_pub_port}...")
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
