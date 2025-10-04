# -*- coding: utf-8 -*-
"""
test_pubsub_visibility.py - Test de visibilidad PUB/SUB
Valida que los eventos se publiquen correctamente en los topics correspondientes
"""

import pytest
import time
import json
import os
from datetime import datetime
from tests.test_utils import TestUtils, SubscriberTester

class TestPubSubVisibility:
    """Test de visibilidad del patrón PUB/SUB"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.gc_endpoint = "tcp://gc:5001"
        self.gc_pub_endpoint = "tcp://gc:5002"
        self.logs_path = "logs/test_pubsub_visibility.txt"
        
        # Crear directorio de logs si no existe
        os.makedirs("logs", exist_ok=True)
        
        # Resultados del test
        self.resultados = {
            "test_name": "test_pubsub_visibility",
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "eventos_devolucion_recibidos": 0,
            "eventos_renovacion_recibidos": 0,
            "tasa_recepcion": 0.0,
            "errores": []
        }
    
    def test_pubsub_devolucion_visibility(self):
        """Test de visibilidad de eventos de devolución"""
        print("\n🔄 Test: Visibilidad PUB/SUB - Devolución")
        
        # 1. Configurar subscriber ANTES de enviar
        subscriber = SubscriberTester(self.gc_pub_endpoint)
        subscriber.conectar(["devolucion"])
        subscriber.iniciar_escucha()
        
        # Esperar slow joiner
        TestUtils.esperar_slow_joiner()
        
        # 2. Enviar solicitud de devolución
        payload = {
            "op": "DEVOLUCION",
            "libro_id": "L003",
            "usuario_id": "U_PUBSUB_TEST_DEV",
            "sede": "SEDE_PUBSUB"
        }
        
        print(f"📤 Enviando solicitud de devolución: {payload}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload)
        
        # 3. Validar ACK
        assert status == "OK", f"ACK debe ser OK, obtuvo: {status}"
        print(f"✅ ACK recibido en {ack_ms:.2f}ms")
        
        # 4. Esperar evento con timeout
        print("⏳ Esperando evento de devolución...")
        time.sleep(3)  # Dar tiempo para procesamiento asíncrono
        
        # 5. Validar recepción de evento
        eventos_devolucion = subscriber.obtener_eventos("DEVOLUCION")
        assert len(eventos_devolucion) > 0, "No se recibió evento de devolución"
        
        evento = eventos_devolucion[0]
        print(f"📨 Evento recibido: {evento}")
        
        # 6. Validar estructura del evento
        data = evento['data']
        assert data['operacion'] == 'DEVOLUCION', f"Operación incorrecta: {data['operacion']}"
        assert data['libro_id'] == payload['libro_id'], f"Libro ID incorrecto: {data['libro_id']}"
        assert data['usuario_id'] == payload['usuario_id'], f"Usuario ID incorrecto: {data['usuario_id']}"
        assert data['sede'] == payload['sede'], f"Sede incorrecta: {data['sede']}"
        assert 'timestamp' in data, "Timestamp faltante en evento"
        
        # Validar timestamp (debe ser reciente)
        timestamp = data['timestamp']
        evento_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        diff_seconds = abs((now - evento_time).total_seconds())
        assert diff_seconds < 10, f"Timestamp muy antiguo: {timestamp}"
        
        print("✅ Evento de devolución válido")
        
        # Limpiar
        subscriber.detener()
        
        # Actualizar resultados
        self.resultados["eventos_devolucion_recibidos"] = len(eventos_devolucion)
    
    def test_pubsub_renovacion_visibility(self):
        """Test de visibilidad de eventos de renovación"""
        print("\n🔄 Test: Visibilidad PUB/SUB - Renovación")
        
        # 1. Configurar subscriber ANTES de enviar
        subscriber = SubscriberTester(self.gc_pub_endpoint)
        subscriber.conectar(["renovacion"])
        subscriber.iniciar_escucha()
        
        # Esperar slow joiner
        TestUtils.esperar_slow_joiner()
        
        # 2. Enviar solicitud de renovación
        payload = {
            "op": "RENOVACION",
            "libro_id": "L001",
            "usuario_id": "U_PUBSUB_TEST_REN",
            "sede": "SEDE_PUBSUB"
        }
        
        print(f"📤 Enviando solicitud de renovación: {payload}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload)
        
        # 3. Validar ACK
        assert status == "OK", f"ACK debe ser OK, obtuvo: {status}"
        print(f"✅ ACK recibido en {ack_ms:.2f}ms")
        
        # 4. Esperar evento con timeout
        print("⏳ Esperando evento de renovación...")
        time.sleep(3)  # Dar tiempo para procesamiento asíncrono
        
        # 5. Validar recepción de evento
        eventos_renovacion = subscriber.obtener_eventos("RENOVACION")
        assert len(eventos_renovacion) > 0, "No se recibió evento de renovación"
        
        evento = eventos_renovacion[0]
        print(f"📨 Evento recibido: {evento}")
        
        # 6. Validar estructura del evento
        data = evento['data']
        assert data['operacion'] == 'RENOVACION', f"Operación incorrecta: {data['operacion']}"
        assert data['libro_id'] == payload['libro_id'], f"Libro ID incorrecto: {data['libro_id']}"
        assert data['usuario_id'] == payload['usuario_id'], f"Usuario ID incorrecto: {data['usuario_id']}"
        assert data['sede'] == payload['sede'], f"Sede incorrecta: {data['sede']}"
        assert 'timestamp' in data, "Timestamp faltante en evento"
        assert 'nueva_fecha_devolucion' in data, "Nueva fecha de devolución faltante"
        
        # Validar nueva fecha de devolución
        nueva_fecha = data['nueva_fecha_devolucion']
        assert TestUtils.validar_fecha_renovacion(nueva_fecha), f"Fecha de renovación inválida: {nueva_fecha}"
        
        # Validar timestamp (debe ser reciente)
        timestamp = data['timestamp']
        evento_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        diff_seconds = abs((now - evento_time).total_seconds())
        assert diff_seconds < 10, f"Timestamp muy antiguo: {timestamp}"
        
        print("✅ Evento de renovación válido")
        
        # Limpiar
        subscriber.detener()
        
        # Actualizar resultados
        self.resultados["eventos_renovacion_recibidos"] = len(eventos_renovacion)
    
    def test_pubsub_multiple_topics(self):
        """Test de suscripción a múltiples topics"""
        print("\n🔄 Test: Suscripción a múltiples topics")
        
        # 1. Configurar subscriber para ambos topics
        subscriber = SubscriberTester(self.gc_pub_endpoint)
        subscriber.conectar(["devolucion", "renovacion"])
        subscriber.iniciar_escucha()
        
        # Esperar slow joiner
        TestUtils.esperar_slow_joiner()
        
        # 2. Enviar una devolución
        payload_dev = {
            "op": "DEVOLUCION",
            "libro_id": "L002",
            "usuario_id": "U_MULTI_TEST_DEV",
            "sede": "SEDE_MULTI"
        }
        
        print(f"📤 Enviando devolución: {payload_dev}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload_dev)
        assert status == "OK", f"ACK devolución debe ser OK, obtuvo: {status}"
        
        # 3. Enviar una renovación
        payload_ren = {
            "op": "RENOVACION",
            "libro_id": "L003",
            "usuario_id": "U_MULTI_TEST_REN",
            "sede": "SEDE_MULTI"
        }
        
        print(f"📤 Enviando renovación: {payload_ren}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload_ren)
        assert status == "OK", f"ACK renovación debe ser OK, obtuvo: {status}"
        
        # 4. Esperar eventos
        print("⏳ Esperando eventos...")
        time.sleep(3)
        
        # 5. Validar recepción de ambos eventos
        eventos_devolucion = subscriber.obtener_eventos("DEVOLUCION")
        eventos_renovacion = subscriber.obtener_eventos("RENOVACION")
        
        print(f"📊 Eventos recibidos - Devolución: {len(eventos_devolucion)}, Renovación: {len(eventos_renovacion)}")
        
        assert len(eventos_devolucion) > 0, "No se recibió evento de devolución"
        assert len(eventos_renovacion) > 0, "No se recibió evento de renovación"
        
        # Validar que los eventos corresponden a las solicitudes enviadas
        dev_evento = eventos_devolucion[0]
        ren_evento = eventos_renovacion[0]
        
        assert dev_evento['data']['libro_id'] == payload_dev['libro_id'], "Libro ID de devolución incorrecto"
        assert ren_evento['data']['libro_id'] == payload_ren['libro_id'], "Libro ID de renovación incorrecto"
        
        print("✅ Ambos eventos recibidos correctamente")
        
        # Limpiar
        subscriber.detener()
        
        # Actualizar resultados
        self.resultados["eventos_devolucion_recibidos"] += len(eventos_devolucion)
        self.resultados["eventos_renovacion_recibidos"] += len(eventos_renovacion)
    
    def teardown_method(self):
        """Limpieza después de cada test"""
        # Calcular tasa de recepción
        total_eventos_esperados = 2  # 1 devolución + 1 renovación en test múltiple
        total_eventos_recibidos = (
            self.resultados["eventos_devolucion_recibidos"] + 
            self.resultados["eventos_renovacion_recibidos"]
        )
        
        if total_eventos_esperados > 0:
            self.resultados["tasa_recepcion"] = (total_eventos_recibidos / total_eventos_esperados) * 100
        
        # Marcar test como pasado si la tasa de recepción es 100%
        self.resultados["passed"] = self.resultados["tasa_recepcion"] == 100.0
        
        # Generar reporte
        TestUtils.generar_reporte_test(
            "test_pubsub_visibility",
            self.resultados,
            self.logs_path
        )
        
        print(f"\n📊 Test completado:")
        print(f"   Eventos devolución recibidos: {self.resultados['eventos_devolucion_recibidos']}")
        print(f"   Eventos renovación recibidos: {self.resultados['eventos_renovacion_recibidos']}")
        print(f"   Tasa de recepción: {self.resultados['tasa_recepcion']:.1f}%")
        print(f"   Estado: {'PASSED' if self.resultados['passed'] else 'FAILED'}")
        print(f"   Reporte: {self.logs_path}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
