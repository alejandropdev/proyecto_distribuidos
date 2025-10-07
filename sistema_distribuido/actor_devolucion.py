#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actor de Devolución - Sistema Distribuido de Préstamo de Libros
Suscribe a eventos de devolución y actualiza la base de datos de libros
"""

import zmq
import json
import time
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ACTOR_DEV - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ActorDevolucion:
    def __init__(self, archivo_libros="data/libros.json"):
        self.context = zmq.Context()
        self.sub_socket = None
        self.archivo_libros = archivo_libros
        self.contador_devoluciones = 0
        self.running = True
        
    def conectar_gestor_carga(self):
        """Conecta al Gestor de Carga usando SUB socket"""
        try:
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect("tcp://gc:5002")
            
            # Suscribirse al topic "devolucion"
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"devolucion")
            
            logger.info("Conectado al Gestor de Carga en tcp://gc:5002")
            logger.info("Suscrito al topic 'devolucion'")
            
            # Pequeña pausa para asegurar la conexión
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error conectando al Gestor de Carga: {e}")
            raise
    
    def cargar_libros(self):
        """Carga la base de datos de libros desde el archivo JSON"""
        try:
            if not os.path.exists(self.archivo_libros):
                logger.error(f"Archivo de libros no encontrado: {self.archivo_libros}")
                return []
            
            with open(self.archivo_libros, 'r', encoding='utf-8') as f:
                base_datos = json.load(f)
            
            # Verificar si es la nueva estructura
            if isinstance(base_datos, dict) and 'libros' in base_datos:
                libros = base_datos['libros']
                logger.info(f"Base de datos de libros cargada: {len(libros)} libros")
                return base_datos
            else:
                # Estructura antigua
                logger.info(f"Base de datos de libros cargada: {len(base_datos)} libros")
                return base_datos
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando archivo de libros: {e}")
            return []
        except Exception as e:
            logger.error(f"Error cargando libros: {e}")
            return []
    
    def guardar_libros(self, libros):
        """Guarda la base de datos de libros al archivo JSON"""
        try:
            # Crear backup del archivo original
            backup_file = f"{self.archivo_libros}.backup"
            if os.path.exists(self.archivo_libros):
                import shutil
                shutil.copy2(self.archivo_libros, backup_file)
            
            # Guardar archivo actualizado
            with open(self.archivo_libros, 'w', encoding='utf-8') as f:
                json.dump(libros, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Base de datos de libros actualizada y guardada")
            
        except Exception as e:
            logger.error(f"Error guardando libros: {e}")
    
    def procesar_devolucion(self, evento):
        """Procesa un evento de devolución"""
        try:
            libro_id = evento.get('libro_id', '')
            usuario_id = evento.get('usuario_id', '')
            sede = evento.get('sede', 'SEDE_1')
            timestamp = evento.get('timestamp', '')
            
            logger.info(f"Procesando devolución: Libro {libro_id} - Usuario {usuario_id} - Sede {sede}")
            
            # Cargar base de datos actual
            base_datos = self.cargar_libros()
            
            if not base_datos or 'libros' not in base_datos:
                logger.error("No se pudo cargar la base de datos de libros")
                return False
            
            libros = base_datos['libros']
            ejemplares = base_datos.get('ejemplares', [])
            
            # Buscar el libro en la base de datos
            libro_encontrado = False
            ejemplar_devuelto = False
            
            for libro in libros:
                if libro.get('libro_id') == libro_id:
                    # Buscar un ejemplar prestado por este usuario en la sede especificada
                    for ejemplar in libro.get('ejemplares', []):
                        if (ejemplar.get('estado') == 'prestado' and 
                            ejemplar.get('usuario_prestamo') == usuario_id and
                            ejemplar.get('sede') == sede):
                            
                            # Marcar ejemplar como disponible
                            ejemplar['estado'] = 'disponible'
                            ejemplar['fecha_devolucion'] = None
                            ejemplar['usuario_prestamo'] = None
                            ejemplar['sede'] = None
                            
                            # Actualizar contadores del libro
                            libro['ejemplares_disponibles'] = libro.get('ejemplares_disponibles', 0) + 1
                            libro['ejemplares_prestados'] = libro.get('ejemplares_prestados', 0) - 1
                            
                            logger.info(f"Ejemplar {ejemplar['ejemplar_id']} devuelto por usuario {usuario_id}")
                            logger.info(f"Ejemplares disponibles: {libro['ejemplares_disponibles']}, Prestados: {libro['ejemplares_prestados']}")
                            
                            ejemplar_devuelto = True
                            break
                    
                    if ejemplar_devuelto:
                        libro_encontrado = True
                        break
            
            if not libro_encontrado:
                logger.warning(f"Libro {libro_id} no encontrado en la base de datos")
                return False
            
            if not ejemplar_devuelto:
                logger.warning(f"No se encontró ejemplar prestado del libro {libro_id} por usuario {usuario_id} en sede {sede}")
                return False
            
            # Actualizar también el array global de ejemplares
            for ejemplar in ejemplares:
                if (ejemplar.get('libro_id') == libro_id and 
                    ejemplar.get('usuario_prestamo') == usuario_id and
                    ejemplar.get('sede') == sede and
                    ejemplar.get('estado') == 'prestado'):
                    ejemplar['estado'] = 'disponible'
                    ejemplar['fecha_devolucion'] = None
                    ejemplar['usuario_prestamo'] = None
                    ejemplar['sede'] = None
                    break
            
            # Actualizar metadata
            base_datos['metadata']['ejemplares_disponibles'] = base_datos['metadata'].get('ejemplares_disponibles', 0) + 1
            if sede == 'SEDE_1':
                base_datos['metadata']['ejemplares_prestados_sede_1'] = base_datos['metadata'].get('ejemplares_prestados_sede_1', 0) - 1
            else:
                base_datos['metadata']['ejemplares_prestados_sede_2'] = base_datos['metadata'].get('ejemplares_prestados_sede_2', 0) - 1
            
            # Guardar cambios
            self.guardar_libros(base_datos)
            
            self.contador_devoluciones += 1
            logger.info(f"Devolución procesada exitosamente (#{self.contador_devoluciones})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando devolución: {e}")
            return False
    
    def escuchar_eventos(self):
        """Escucha eventos de devolución del Gestor de Carga"""
        logger.info("Iniciando escucha de eventos de devolución...")
        
        while self.running:
            try:
                # Recibir mensaje (topic + datos)
                mensaje = self.sub_socket.recv_multipart(zmq.NOBLOCK)
                
                if len(mensaje) >= 2:
                    topic = mensaje[0].decode('utf-8')
                    datos_json = mensaje[1].decode('utf-8')
                    
                    logger.info(f"Evento recibido - Topic: {topic}")
                    logger.info(f"Datos: {datos_json}")
                    
                    # Parsear evento
                    evento = json.loads(datos_json)
                    
                    # Procesar solo eventos de devolución
                    if topic == "devolucion" and evento.get('operacion') == 'DEVOLUCION':
                        self.procesar_devolucion(evento)
                    else:
                        logger.warning(f"Evento inesperado recibido: {topic} - {evento.get('operacion', 'N/A')}")
                
            except zmq.Again:
                # No hay mensajes disponibles, continuar
                time.sleep(0.1)
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando evento JSON: {e}")
                continue
            except Exception as e:
                logger.error(f"Error escuchando eventos: {e}")
                time.sleep(1)
    
    def iniciar(self):
        """Inicia el Actor de Devolución"""
        try:
            logger.info("Iniciando Actor de Devolución...")
            
            # Conectar al Gestor de Carga
            self.conectar_gestor_carga()
            
            # Verificar que existe el archivo de libros
            if not os.path.exists(self.archivo_libros):
                logger.error(f"Archivo de libros no encontrado: {self.archivo_libros}")
                return
            
            logger.info("Actor de Devolución iniciado correctamente")
            logger.info("Esperando eventos de devolución...")
            
            # Iniciar escucha de eventos
            self.escuchar_eventos()
            
        except KeyboardInterrupt:
            logger.info("Deteniendo Actor de Devolución...")
            self.detener()
        except Exception as e:
            logger.error(f"Error fatal en Actor de Devolución: {e}")
            self.detener()
    
    def detener(self):
        """Detiene el Actor de Devolución"""
        self.running = False
        
        if self.sub_socket:
            self.sub_socket.close()
        if self.context:
            self.context.term()
        
        logger.info(f"Total de devoluciones procesadas: {self.contador_devoluciones}")
        logger.info("Actor de Devolución detenido")

def main():
    """Función principal"""
    actor = ActorDevolucion()
    actor.iniciar()

if __name__ == "__main__":
    main()
