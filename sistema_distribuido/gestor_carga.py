#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Carga (GC) - Sistema Distribuido de Préstamo de Libros
Maneja las solicitudes de renovación y devolución usando ZeroMQ REQ/REP y PUB/SUB
"""

import zmq
import json
import threading
import time
from datetime import datetime, timedelta
import logging

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
        self.rep_socket = None
        self.pub_socket = None
        self.contador_operaciones = 0
        self.running = True
        
    def inicializar_sockets(self):
        """Inicializa los sockets REQ/REP y PUB/SUB"""
        try:
            # Socket REP para recibir solicitudes del Proceso Solicitante
            self.rep_socket = self.context.socket(zmq.REP)
            self.rep_socket.bind("tcp://0.0.0.0:5001")
            logger.info("✅ Socket REP inicializado en tcp://0.0.0.0:5001")
            
            # Socket PUB para enviar eventos a los actores
            self.pub_socket = self.context.socket(zmq.PUB)
            self.pub_socket.bind("tcp://0.0.0.0:5002")
            logger.info("✅ Socket PUB inicializado en tcp://0.0.0.0:5002")
            
            # Pequeña pausa para asegurar que los sockets estén listos
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sockets: {e}")
            raise
    
    def procesar_solicitud(self, mensaje_json):
        """Procesa una solicitud y genera el evento correspondiente"""
        try:
            datos = json.loads(mensaje_json)
            operacion = datos.get('op', '').upper()
            libro_id = datos.get('libro_id', '')
            usuario_id = datos.get('usuario_id', '')
            sede = datos.get('sede', 'SEDE_1')
            
            if operacion not in ['RENOVACION', 'DEVOLUCION']:
                return {
                    "status": "ERROR",
                    "message": f"Operación inválida: {operacion}. Solo se permiten RENOVACION y DEVOLUCION"
                }
            
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
            logger.info(f"📝 Operación #{self.contador_operaciones} procesada: {operacion} - Libro {libro_id} - Usuario {usuario_id}")
            
            return {
                "status": "OK",
                "message": "Recibido. Procesando...",
                "operacion": operacion,
                "libro_id": libro_id
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            return {
                "status": "ERROR",
                "message": "Formato JSON inválido"
            }
        except Exception as e:
            logger.error(f"❌ Error procesando solicitud: {e}")
            return {
                "status": "ERROR",
                "message": f"Error interno: {str(e)}"
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
            
            logger.info(f"📡 Evento enviado a actores - Topic: {topic} - Evento: {evento}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando evento a actores: {e}")
    
    def manejar_solicitudes(self):
        """Maneja las solicitudes entrantes del Proceso Solicitante"""
        logger.info("🔄 Iniciando manejo de solicitudes...")
        
        while self.running:
            try:
                # Recibir solicitud del Proceso Solicitante
                mensaje = self.rep_socket.recv(zmq.NOBLOCK)
                mensaje_str = mensaje.decode('utf-8')
                
                logger.info(f"📨 Solicitud recibida: {mensaje_str}")
                
                # Procesar solicitud
                respuesta = self.procesar_solicitud(mensaje_str)
                
                # Enviar respuesta inmediata (REQ/REP pattern)
                respuesta_json = json.dumps(respuesta, ensure_ascii=False)
                self.rep_socket.send(respuesta_json.encode('utf-8'))
                
                logger.info(f"📤 Respuesta enviada: {respuesta_json}")
                
            except zmq.Again:
                # No hay mensajes disponibles, continuar
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"❌ Error manejando solicitudes: {e}")
                time.sleep(1)
    
    def iniciar(self):
        """Inicia el Gestor de Carga"""
        try:
            logger.info("🚀 Iniciando Gestor de Carga...")
            self.inicializar_sockets()
            
            logger.info("✅ Gestor de Carga iniciado correctamente")
            logger.info("📊 Esperando solicitudes en puerto 5001...")
            logger.info("📡 Listo para publicar eventos en puerto 5002...")
            
            # Iniciar manejo de solicitudes
            self.manejar_solicitudes()
            
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo Gestor de Carga...")
            self.detener()
        except Exception as e:
            logger.error(f"❌ Error fatal en Gestor de Carga: {e}")
            self.detener()
    
    def detener(self):
        """Detiene el Gestor de Carga"""
        self.running = False
        
        if self.rep_socket:
            self.rep_socket.close()
        if self.pub_socket:
            self.pub_socket.close()
        if self.context:
            self.context.term()
        
        logger.info(f"📊 Total de operaciones procesadas: {self.contador_operaciones}")
        logger.info("✅ Gestor de Carga detenido")

def main():
    """Función principal"""
    gc = GestorCarga()
    gc.iniciar()

if __name__ == "__main__":
    main()
