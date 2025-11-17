#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actor de Préstamo - Sistema Distribuido de Préstamo de Libros
Procesa solicitudes de préstamo usando REQ/REP con GC y GA
"""

import zmq
import json
import time
import os
import logging
from utils_failover import FailoverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ACTOR_PRESTAMO - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ActorPrestamo:
    def __init__(self):
        """Inicializa el Actor de Préstamo"""
        self.context = zmq.Context()
        self.rep_socket = None  # Socket REP para recibir solicitudes de GC
        self.failover_manager = None
        self.contador_prestamos = 0
        self.contador_exitosos = 0
        self.contador_errores = 0
        self.running = True
        
        # Leer variables de entorno
        self.gc_host = os.getenv('GC_HOST', 'gc')
        self.gc_port = int(os.getenv('GC_ACTOR_PRESTAMO_PORT', '5004'))
        self.ga_host = os.getenv('GA_HOST', 'ga')
        self.ga_port = int(os.getenv('GA_PORT', '5003'))
        
        # Inicializar failover manager
        self.failover_manager = FailoverManager(
            ga_host=self.ga_host,
            ga_port=self.ga_port,
            timeout=5,
            retry_interval=30
        )
    
    def inicializar_socket(self):
        """Inicializa el socket REP para recibir solicitudes de GC"""
        try:
            self.rep_socket = self.context.socket(zmq.REP)
            bind_address = f"tcp://0.0.0.0:{self.gc_port}"
            self.rep_socket.bind(bind_address)
            logger.info(f"Socket REP inicializado en {bind_address}")
            
            # Pequeña pausa para asegurar que el socket esté listo
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error inicializando socket: {e}")
            raise
    
    def procesar_prestamo(self, solicitud):
        """
        Procesa una solicitud de préstamo
        
        Args:
            solicitud: Dict con libro_id, usuario_id, sede, y opcionalmente search_criteria
        
        Returns:
            Dict con resultado: {"success": bool, "message": str, ...}
        """
        libro_id = solicitud.get('libro_id')
        usuario_id = solicitud.get('usuario_id')
        sede = solicitud.get('sede', 'SEDE_1')
        search_criteria = solicitud.get('search_criteria')
        
        logger.info(f"Procesando préstamo: Libro {libro_id}, Usuario {usuario_id}, Sede {sede}")
        
        # Verificar conexión con GA
        health = self.failover_manager.verificar_y_reconectar()
        if not health.get('ok'):
            logger.error("GA no está disponible")
            return {
                "success": False,
                "message": "Error: Gestor de Almacenamiento no disponible"
            }
        
        # Si hay search_criteria pero no libro_id, buscar primero
        if search_criteria and not libro_id:
            logger.info(f"Buscando libro por criterios: {search_criteria}")
            resultado_busqueda = self.failover_manager.enviar_operacion(
                "GET_BOOK",
                {"libro_id": None, "search_criteria": search_criteria}
            )
            
            if resultado_busqueda and resultado_busqueda.get('success'):
                libro_id = resultado_busqueda.get('libro', {}).get('libro_id')
                logger.info(f"Libro encontrado: {libro_id}")
            else:
                return {
                    "success": False,
                    "message": "Libro no encontrado con los criterios especificados"
                }
        
        # Validar que tenemos libro_id
        if not libro_id:
            return {
                "success": False,
                "message": "Se requiere libro_id o criterios de búsqueda"
            }
        
        # Verificar disponibilidad del libro
        resultado_verificacion = self.failover_manager.enviar_operacion(
            "GET_BOOK",
            {"libro_id": libro_id}
        )
        
        if not resultado_verificacion or not resultado_verificacion.get('success'):
            return {
                "success": False,
                "message": f"Libro {libro_id} no encontrado en la base de datos"
            }
        
        libro = resultado_verificacion.get('libro', {})
        ejemplares_disponibles = libro.get('ejemplares_disponibles', 0)
        
        if ejemplares_disponibles <= 0:
            return {
                "success": False,
                "message": f"No hay ejemplares disponibles del libro {libro_id}"
            }
        
        # Realizar el préstamo
        resultado_prestamo = self.failover_manager.enviar_operacion(
            "LOAN_BOOK",
            {
                "libro_id": libro_id,
                "usuario_id": usuario_id,
                "sede": sede
            }
        )
        
        if not resultado_prestamo:
            return {
                "success": False,
                "message": "Error comunicándose con el Gestor de Almacenamiento"
            }
        
        if resultado_prestamo.get('success'):
            self.contador_exitosos += 1
            logger.info(f"Préstamo exitoso: {resultado_prestamo.get('message')}")
            return {
                "success": True,
                "message": resultado_prestamo.get('message'),
                "ejemplar_id": resultado_prestamo.get('ejemplar_id'),
                "fecha_devolucion": resultado_prestamo.get('fecha_devolucion'),
                "libro_id": libro_id,
                "titulo": libro.get('titulo', 'N/A')
            }
        else:
            self.contador_errores += 1
            logger.error(f"Error en préstamo: {resultado_prestamo.get('message')}")
            return {
                "success": False,
                "message": resultado_prestamo.get('message')
            }
    
    def procesar_solicitud(self, mensaje_json):
        """
        Procesa una solicitud recibida de GC
        
        Args:
            mensaje_json: JSON string con la solicitud
        
        Returns:
            JSON string con la respuesta
        """
        try:
            solicitud = json.loads(mensaje_json)
            operacion = solicitud.get('operacion', '').upper()
            
            if operacion != 'PRESTAMO':
                return json.dumps({
                    "success": False,
                    "message": f"Operación inválida: {operacion}. Solo se permite PRESTAMO"
                }, ensure_ascii=False)
            
            # Procesar préstamo
            resultado = self.procesar_prestamo(solicitud)
            
            self.contador_prestamos += 1
            logger.info(f"Préstamo procesado #{self.contador_prestamos}: {resultado.get('success')}")
            
            return json.dumps(resultado, ensure_ascii=False)
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            return json.dumps({
                "success": False,
                "message": "Formato JSON inválido"
            }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error procesando solicitud: {e}")
            return json.dumps({
                "success": False,
                "message": f"Error interno: {str(e)}"
            }, ensure_ascii=False)
    
    def manejar_solicitudes(self):
        """Maneja las solicitudes entrantes de GC"""
        logger.info("Iniciando manejo de solicitudes de préstamo...")
        
        while self.running:
            try:
                # Recibir solicitud de GC
                mensaje = self.rep_socket.recv(zmq.NOBLOCK)
                mensaje_str = mensaje.decode('utf-8')
                
                logger.info(f"Solicitud recibida de GC: {mensaje_str}")
                
                # Procesar solicitud
                respuesta = self.procesar_solicitud(mensaje_str)
                
                # Enviar respuesta a GC
                self.rep_socket.send(respuesta.encode('utf-8'))
                
                logger.info(f"Respuesta enviada a GC: {respuesta}")
                
            except zmq.Again:
                # No hay mensajes disponibles
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"Error manejando solicitudes: {e}")
                time.sleep(1)
    
    def iniciar(self):
        """Inicia el Actor de Préstamo"""
        try:
            logger.info("Iniciando Actor de Préstamo...")
            self.inicializar_socket()
            
            logger.info("Actor de Préstamo iniciado correctamente")
            logger.info(f"Esperando solicitudes de GC en puerto {self.gc_port}...")
            logger.info(f"Conectado a GA en {self.ga_host}:{self.ga_port}")
            
            self.manejar_solicitudes()
            
        except KeyboardInterrupt:
            logger.info("Deteniendo Actor de Préstamo...")
            self.detener()
        except Exception as e:
            logger.error(f"Error fatal en Actor de Préstamo: {e}")
            self.detener()
    
    def detener(self):
        """Detiene el Actor de Préstamo"""
        self.running = False
        
        if self.failover_manager:
            self.failover_manager.cerrar()
        
        if self.rep_socket:
            self.rep_socket.close()
        if self.context:
            self.context.term()
        
        logger.info(f"Total de préstamos procesados: {self.contador_prestamos}")
        logger.info(f"Préstamos exitosos: {self.contador_exitosos}")
        logger.info(f"Préstamos con error: {self.contador_errores}")
        logger.info("Actor de Préstamo detenido")

def main():
    """Función principal"""
    actor = ActorPrestamo()
    actor.iniciar()

if __name__ == "__main__":
    main()

