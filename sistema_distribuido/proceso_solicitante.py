#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proceso Solicitante (PS) - Sistema Distribuido de Préstamo de Libros
Envía solicitudes de renovación y devolución al Gestor de Carga
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
    format='%(asctime)s - PS - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProcesoSolicitante:
    def __init__(self):
        self.context = zmq.Context()
        self.req_socket = None
        self.contador_solicitudes = 0
        self.contador_exitosos = 0
        self.contador_errores = 0
        
    def conectar_gestor_carga(self):
        """Conecta al Gestor de Carga usando REQ socket"""
        try:
            self.req_socket = self.context.socket(zmq.REQ)
            self.req_socket.connect("tcp://gc:5001")
            logger.info("✅ Conectado al Gestor de Carga en tcp://gc:5001")
            
            # Pequeña pausa para asegurar la conexión
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Error conectando al Gestor de Carga: {e}")
            raise
    
    def leer_solicitudes(self, archivo_solicitudes):
        """Lee las solicitudes desde el archivo de texto"""
        solicitudes = []
        
        try:
            if not os.path.exists(archivo_solicitudes):
                logger.error(f"❌ Archivo de solicitudes no encontrado: {archivo_solicitudes}")
                return solicitudes
            
            with open(archivo_solicitudes, 'r', encoding='utf-8') as f:
                for numero_linea, linea in enumerate(f, 1):
                    linea = linea.strip()
                    if not linea or linea.startswith('#'):
                        continue
                    
                    # Parsear línea: OPERACION LIBRO_ID USUARIO_ID
                    partes = linea.split()
                    if len(partes) >= 3:
                        operacion = partes[0].upper()
                        libro_id = partes[1]
                        usuario_id = partes[2]
                        sede = partes[3] if len(partes) > 3 else "SEDE_1"
                        
                        solicitud = {
                            "op": operacion,
                            "libro_id": libro_id,
                            "usuario_id": usuario_id,
                            "sede": sede,
                            "linea": numero_linea
                        }
                        solicitudes.append(solicitud)
                    else:
                        logger.warning(f"⚠️ Línea {numero_linea} mal formateada: {linea}")
            
            logger.info(f"📖 Leídas {len(solicitudes)} solicitudes desde {archivo_solicitudes}")
            return solicitudes
            
        except Exception as e:
            logger.error(f"❌ Error leyendo archivo de solicitudes: {e}")
            return solicitudes
    
    def enviar_solicitud(self, solicitud):
        """Envía una solicitud al Gestor de Carga"""
        try:
            # Crear mensaje JSON
            mensaje = {
                "op": solicitud["op"],
                "libro_id": solicitud["libro_id"],
                "usuario_id": solicitud["usuario_id"],
                "sede": solicitud["sede"]
            }
            
            mensaje_json = json.dumps(mensaje, ensure_ascii=False)
            
            # Enviar solicitud
            self.req_socket.send(mensaje_json.encode('utf-8'))
            logger.info(f"📤 Solicitud #{self.contador_solicitudes + 1} enviada: {mensaje_json}")
            
            # Recibir respuesta
            respuesta_bytes = self.req_socket.recv()
            respuesta_str = respuesta_bytes.decode('utf-8')
            respuesta = json.loads(respuesta_str)
            
            logger.info(f"📥 Respuesta recibida: {respuesta_str}")
            
            # Procesar respuesta
            if respuesta.get("status") == "OK":
                self.contador_exitosos += 1
                logger.info(f"✅ Solicitud procesada exitosamente")
            else:
                self.contador_errores += 1
                logger.error(f"❌ Error en solicitud: {respuesta.get('message', 'Error desconocido')}")
            
            self.contador_solicitudes += 1
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando respuesta JSON: {e}")
            self.contador_errores += 1
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando solicitud: {e}")
            self.contador_errores += 1
            return False
    
    def procesar_solicitudes(self, archivo_solicitudes):
        """Procesa todas las solicitudes del archivo"""
        logger.info("🔄 Iniciando procesamiento de solicitudes...")
        
        # Leer solicitudes
        solicitudes = self.leer_solicitudes(archivo_solicitudes)
        
        if not solicitudes:
            logger.warning("⚠️ No hay solicitudes para procesar")
            return
        
        logger.info(f"📊 Procesando {len(solicitudes)} solicitudes...")
        
        # Procesar cada solicitud
        for i, solicitud in enumerate(solicitudes, 1):
            try:
                logger.info(f"🔄 Procesando solicitud {i}/{len(solicitudes)}: {solicitud['op']} - {solicitud['libro_id']} - {solicitud['usuario_id']}")
                
                # Enviar solicitud
                exito = self.enviar_solicitud(solicitud)
                
                if exito:
                    logger.info(f"✅ Solicitud {i} completada")
                else:
                    logger.error(f"❌ Solicitud {i} falló")
                
                # Pausa entre solicitudes (simular carga de trabajo real)
                if i < len(solicitudes):  # No pausar después de la última solicitud
                    logger.info("⏳ Esperando 1 segundo antes de la siguiente solicitud...")
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Interrupción detectada, deteniendo procesamiento...")
                break
            except Exception as e:
                logger.error(f"❌ Error procesando solicitud {i}: {e}")
                self.contador_errores += 1
                continue
        
        # Mostrar estadísticas finales
        self.mostrar_estadisticas()
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del procesamiento"""
        logger.info("📊 ===== ESTADÍSTICAS FINALES =====")
        logger.info(f"📤 Total de solicitudes enviadas: {self.contador_solicitudes}")
        logger.info(f"✅ Solicitudes exitosas: {self.contador_exitosos}")
        logger.info(f"❌ Solicitudes con error: {self.contador_errores}")
        
        if self.contador_solicitudes > 0:
            porcentaje_exito = (self.contador_exitosos / self.contador_solicitudes) * 100
            logger.info(f"📈 Porcentaje de éxito: {porcentaje_exito:.1f}%")
        
        logger.info("📊 ================================")
    
    def iniciar(self, archivo_solicitudes="data/solicitudes.txt"):
        """Inicia el Proceso Solicitante"""
        try:
            logger.info("🚀 Iniciando Proceso Solicitante...")
            
            # Conectar al Gestor de Carga
            self.conectar_gestor_carga()
            
            # Procesar solicitudes
            self.procesar_solicitudes(archivo_solicitudes)
            
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo Proceso Solicitante...")
        except Exception as e:
            logger.error(f"❌ Error fatal en Proceso Solicitante: {e}")
        finally:
            self.detener()
    
    def detener(self):
        """Detiene el Proceso Solicitante"""
        if self.req_socket:
            self.req_socket.close()
        if self.context:
            self.context.term()
        
        logger.info("✅ Proceso Solicitante detenido")

def main():
    """Función principal"""
    ps = ProcesoSolicitante()
    ps.iniciar()

if __name__ == "__main__":
    main()
