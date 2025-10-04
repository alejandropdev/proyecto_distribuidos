#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actor de Renovación - Sistema Distribuido de Préstamo de Libros
Suscribe a eventos de renovación y actualiza las fechas de devolución
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
    format='%(asctime)s - ACTOR_REN - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ActorRenovacion:
    def __init__(self, archivo_libros="data/libros.json"):
        self.context = zmq.Context()
        self.sub_socket = None
        self.archivo_libros = archivo_libros
        self.contador_renovaciones = 0
        self.running = True
        
    def conectar_gestor_carga(self):
        """Conecta al Gestor de Carga usando SUB socket"""
        try:
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect("tcp://gc:5002")
            
            # Suscribirse al topic "renovacion"
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"renovacion")
            
            logger.info("✅ Conectado al Gestor de Carga en tcp://gc:5002")
            logger.info("📡 Suscrito al topic 'renovacion'")
            
            # Pequeña pausa para asegurar la conexión
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Error conectando al Gestor de Carga: {e}")
            raise
    
    def cargar_libros(self):
        """Carga la base de datos de libros desde el archivo JSON"""
        try:
            if not os.path.exists(self.archivo_libros):
                logger.error(f"❌ Archivo de libros no encontrado: {self.archivo_libros}")
                return []
            
            with open(self.archivo_libros, 'r', encoding='utf-8') as f:
                libros = json.load(f)
            
            logger.info(f"📚 Base de datos de libros cargada: {len(libros)} libros")
            return libros
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando archivo de libros: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error cargando libros: {e}")
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
            
            logger.info(f"💾 Base de datos de libros actualizada y guardada")
            
        except Exception as e:
            logger.error(f"❌ Error guardando libros: {e}")
    
    def procesar_renovacion(self, evento):
        """Procesa un evento de renovación"""
        try:
            libro_id = evento.get('libro_id', '')
            usuario_id = evento.get('usuario_id', '')
            nueva_fecha = evento.get('nueva_fecha_devolucion', '')
            timestamp = evento.get('timestamp', '')
            
            logger.info(f"🔄 Procesando renovación: Libro {libro_id} - Usuario {usuario_id}")
            logger.info(f"📅 Nueva fecha de devolución: {nueva_fecha}")
            
            # Cargar base de datos actual
            libros = self.cargar_libros()
            
            if not libros:
                logger.error("❌ No se pudo cargar la base de datos de libros")
                return False
            
            # Buscar el libro en la base de datos
            libro_encontrado = False
            for libro in libros:
                if libro.get('libro_id') == libro_id:
                    # Actualizar fecha de devolución
                    fecha_anterior = libro.get('fecha_devolucion', 'N/A')
                    libro['fecha_devolucion'] = nueva_fecha
                    
                    logger.info(f"📚 Libro {libro_id} renovado por usuario {usuario_id}")
                    logger.info(f"📅 Fecha de devolución actualizada: {fecha_anterior} → {nueva_fecha}")
                    
                    libro_encontrado = True
                    break
            
            if not libro_encontrado:
                logger.warning(f"⚠️ Libro {libro_id} no encontrado en la base de datos")
                return False
            
            # Guardar cambios
            self.guardar_libros(libros)
            
            self.contador_renovaciones += 1
            logger.info(f"✅ Renovación procesada exitosamente (#{self.contador_renovaciones})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando renovación: {e}")
            return False
    
    def escuchar_eventos(self):
        """Escucha eventos de renovación del Gestor de Carga"""
        logger.info("🔄 Iniciando escucha de eventos de renovación...")
        
        while self.running:
            try:
                # Recibir mensaje (topic + datos)
                mensaje = self.sub_socket.recv_multipart(zmq.NOBLOCK)
                
                if len(mensaje) >= 2:
                    topic = mensaje[0].decode('utf-8')
                    datos_json = mensaje[1].decode('utf-8')
                    
                    logger.info(f"📨 Evento recibido - Topic: {topic}")
                    logger.info(f"📄 Datos: {datos_json}")
                    
                    # Parsear evento
                    evento = json.loads(datos_json)
                    
                    # Procesar solo eventos de renovación
                    if topic == "renovacion" and evento.get('operacion') == 'RENOVACION':
                        self.procesar_renovacion(evento)
                    else:
                        logger.warning(f"⚠️ Evento inesperado recibido: {topic} - {evento.get('operacion', 'N/A')}")
                
            except zmq.Again:
                # No hay mensajes disponibles, continuar
                time.sleep(0.1)
                continue
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parseando evento JSON: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Error escuchando eventos: {e}")
                time.sleep(1)
    
    def iniciar(self):
        """Inicia el Actor de Renovación"""
        try:
            logger.info("🚀 Iniciando Actor de Renovación...")
            
            # Conectar al Gestor de Carga
            self.conectar_gestor_carga()
            
            # Verificar que existe el archivo de libros
            if not os.path.exists(self.archivo_libros):
                logger.error(f"❌ Archivo de libros no encontrado: {self.archivo_libros}")
                return
            
            logger.info("✅ Actor de Renovación iniciado correctamente")
            logger.info("📡 Esperando eventos de renovación...")
            
            # Iniciar escucha de eventos
            self.escuchar_eventos()
            
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo Actor de Renovación...")
            self.detener()
        except Exception as e:
            logger.error(f"❌ Error fatal en Actor de Renovación: {e}")
            self.detener()
    
    def detener(self):
        """Detiene el Actor de Renovación"""
        self.running = False
        
        if self.sub_socket:
            self.sub_socket.close()
        if self.context:
            self.context.term()
        
        logger.info(f"📊 Total de renovaciones procesadas: {self.contador_renovaciones}")
        logger.info("✅ Actor de Renovación detenido")

def main():
    """Función principal"""
    actor = ActorRenovacion()
    actor.iniciar()

if __name__ == "__main__":
    main()
