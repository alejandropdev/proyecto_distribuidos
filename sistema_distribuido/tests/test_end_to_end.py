# -*- coding: utf-8 -*-
"""
test_end_to_end.py - Test end-to-end básico sin PS
Valida comunicación REQ/REP, PUB/SUB y actualización de base de datos
"""

import pytest
import time
import json
import os
from datetime import datetime, timedelta
from tests.test_utils import TestUtils, SubscriberTester

class TestEndToEnd:
    """Test end-to-end del sistema distribuido"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.gc_endpoint = "tcp://gc:5001"
        self.gc_pub_endpoint = "tcp://gc:5002"
        self.libros_path = "data/libros.json"
        self.logs_path = "logs/test_end_to_end.txt"
        
        # Crear directorio de logs si no existe
        os.makedirs("logs", exist_ok=True)
        
        # Resultados del test
        self.resultados = {
            "test_name": "test_end_to_end",
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "operaciones_procesadas": 0,
            "tiempo_ack_promedio": 0.0,
            "errores": []
        }
    
    def test_devolucion_end_to_end(self):
        """Test completo de operación de devolución"""
        print("\nTest: Devolución end-to-end")
        
        # 1. Crear snapshot inicial
        snapshot_path = "logs/libros_before_devolucion.json"
        TestUtils.crear_snapshot_libros(self.libros_path, snapshot_path)
        libros_inicial = TestUtils.read_json(self.libros_path)
        
        # Usar un libro diferente para evitar conflictos con pruebas anteriores
        libro_id = "L003"  # Cambiar a L003 que tiene menos modificaciones
        ejemplares_iniciales = next(
            (l.get('ejemplares_disponibles', 0) for l in libros_inicial if l.get('libro_id') == libro_id), 0
        )
        print(f"Estado inicial - Libro {libro_id}: {ejemplares_iniciales} ejemplares")
        
        # 2. Configurar subscriber para eventos de devolución
        subscriber = SubscriberTester(self.gc_pub_endpoint)
        subscriber.conectar(["devolucion"])
        subscriber.iniciar_escucha()
        
        # Esperar slow joiner
        TestUtils.esperar_slow_joiner()
        
        # 3. Enviar solicitud de devolución
        usuario_id = "U_TEST_DEV"
        
        payload = {
            "op": "DEVOLUCION",
            "libro_id": libro_id,
            "usuario_id": usuario_id,
            "sede": "SEDE_TEST"
        }
        
        print(f"Enviando solicitud de devolución: {payload}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload)
        
        # 4. Validar ACK inmediato
        assert status in ["OK", "ERROR"], f"Status inesperado: {status}"
        assert ack_ms < 500, f"ACK tardó {ack_ms}ms, debe ser < 500ms"
        
        print(f"ACK recibido en {ack_ms:.2f}ms")
        
        # 5. Esperar evento PUB/SUB
        print("Esperando evento de devolución...")
        time.sleep(2)  # Dar tiempo para procesamiento asíncrono
        
        eventos_devolucion = subscriber.obtener_eventos("DEVOLUCION")
        assert len(eventos_devolucion) > 0, "No se recibió evento de devolución"
        
        evento = eventos_devolucion[0]
        assert evento['data']['libro_id'] == libro_id, f"Libro ID no coincide: {evento['data']['libro_id']} != {libro_id}"
        assert evento['data']['usuario_id'] == usuario_id, f"Usuario ID no coincide"
        
        print(f"Evento recibido: {evento['data']}")
        
        # 6. Validar actualización de base de datos
        print("Esperando actualización de base de datos...")
        
        def validar_incremento_ejemplares(libros_actual):
            for libro in libros_actual:
                if libro.get('libro_id') == libro_id:
                    ejemplares_actuales = libro.get('ejemplares_disponibles', 0)
                    print(f"Estado actual - Libro {libro_id}: {ejemplares_actuales} ejemplares (inicial: {ejemplares_iniciales})")
                    return ejemplares_actuales > ejemplares_iniciales
            return False
        
        # Esperar un momento para que el actor procese
        time.sleep(3)
        
        # Verificar cambio directamente
        libros_final = TestUtils.read_json(self.libros_path)
        cambio_detectado = False
        
        for libro in libros_final:
            if libro.get('libro_id') == libro_id:
                ejemplares_actuales = libro.get('ejemplares_disponibles', 0)
                print(f"Estado final - Libro {libro_id}: {ejemplares_actuales} ejemplares (inicial: {ejemplares_iniciales})")
                if ejemplares_actuales > ejemplares_iniciales:
                    cambio_detectado = True
                    break
        
        assert cambio_detectado, f"No se detectó incremento en ejemplares disponibles. Inicial: {ejemplares_iniciales}, Final: {ejemplares_actuales}"
        
        # Verificar cambio específico
        libros_final = TestUtils.read_json(self.libros_path)
        for libro in libros_final:
            if libro.get('libro_id') == libro_id:
                ejemplares_finales = libro.get('ejemplares_disponibles', 0)
                ejemplares_iniciales = next(
                    (l.get('ejemplares_disponibles', 0) for l in libros_inicial if l.get('libro_id') == libro_id), 0
                )
                assert ejemplares_finales == ejemplares_iniciales + 1, \
                    f"Ejemplares no incrementaron correctamente: {ejemplares_iniciales} -> {ejemplares_finales}"
                break
        
        print("Base de datos actualizada correctamente")
        
        # Limpiar
        subscriber.detener()
        
        # Actualizar resultados
        self.resultados["operaciones_procesadas"] += 1
        self.resultados["tiempo_ack_promedio"] = ack_ms
    
    def test_renovacion_end_to_end(self):
        """Test completo de operación de renovación"""
        print("\nTest: Renovación end-to-end")
        
        # 1. Crear snapshot inicial
        snapshot_path = "logs/libros_before_renovacion.json"
        TestUtils.crear_snapshot_libros(self.libros_path, snapshot_path)
        libros_inicial = TestUtils.read_json(self.libros_path)
        
        # Usar un libro diferente para evitar conflictos con pruebas anteriores
        libro_id = "L002"  # Cambiar a L002 para renovación
        fecha_inicial = next(
            (l.get('fecha_devolucion', '') for l in libros_inicial if l.get('libro_id') == libro_id), ''
        )
        print(f"Estado inicial - Libro {libro_id}: fecha {fecha_inicial}")
        
        # 2. Configurar subscriber para eventos de renovación
        subscriber = SubscriberTester(self.gc_pub_endpoint)
        subscriber.conectar(["renovacion"])
        subscriber.iniciar_escucha()
        
        # Esperar slow joiner
        TestUtils.esperar_slow_joiner()
        
        # 3. Enviar solicitud de renovación
        usuario_id = "U_TEST_REN"
        
        payload = {
            "op": "RENOVACION",
            "libro_id": libro_id,
            "usuario_id": usuario_id,
            "sede": "SEDE_TEST"
        }
        
        print(f"Enviando solicitud de renovación: {payload}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload)
        
        # 4. Validar ACK inmediato
        assert status in ["OK", "ERROR"], f"Status inesperado: {status}"
        assert ack_ms < 500, f"ACK tardó {ack_ms}ms, debe ser < 500ms"
        
        print(f"ACK recibido en {ack_ms:.2f}ms")
        
        # 5. Esperar evento PUB/SUB
        print("Esperando evento de renovación...")
        time.sleep(2)  # Dar tiempo para procesamiento asíncrono
        
        eventos_renovacion = subscriber.obtener_eventos("RENOVACION")
        assert len(eventos_renovacion) > 0, "No se recibió evento de renovación"
        
        evento = eventos_renovacion[0]
        assert evento['data']['libro_id'] == libro_id, f"Libro ID no coincide: {evento['data']['libro_id']} != {libro_id}"
        assert evento['data']['usuario_id'] == usuario_id, f"Usuario ID no coincide"
        
        # Validar nueva fecha de devolución
        nueva_fecha = evento['data'].get('nueva_fecha_devolucion')
        assert nueva_fecha is not None, "No se proporcionó nueva fecha de devolución"
        assert TestUtils.validar_fecha_renovacion(nueva_fecha), f"Fecha de renovación inválida: {nueva_fecha}"
        
        print(f"Evento recibido: {evento['data']}")
        
        # 6. Validar actualización de base de datos
        print("Esperando actualización de fecha de devolución...")
        
        def validar_fecha_actualizada(libros_actual):
            for libro in libros_actual:
                if libro.get('libro_id') == libro_id:
                    fecha_actual = libro.get('fecha_devolucion', '')
                    print(f"Estado actual - Libro {libro_id}: fecha {fecha_actual} (inicial: {fecha_inicial}, esperada: {nueva_fecha})")
                    return fecha_actual != fecha_inicial and fecha_actual == nueva_fecha
            return False
        
        # Esperar un momento para que el actor procese
        time.sleep(3)
        
        # Verificar cambio directamente
        libros_final = TestUtils.read_json(self.libros_path)
        cambio_detectado = False
        
        for libro in libros_final:
            if libro.get('libro_id') == libro_id:
                fecha_actual = libro.get('fecha_devolucion', '')
                print(f"Estado final - Libro {libro_id}: fecha {fecha_actual} (inicial: {fecha_inicial}, esperada: {nueva_fecha})")
                # Verificar que la fecha actual coincide con la fecha esperada del evento
                if fecha_actual == nueva_fecha:
                    cambio_detectado = True
                    break
        
        assert cambio_detectado, f"No se detectó actualización de fecha de devolución. Final: {fecha_actual}, Esperada: {nueva_fecha}"
        
        # Verificar cambio específico
        libros_final = TestUtils.read_json(self.libros_path)
        for libro in libros_final:
            if libro.get('libro_id') == libro_id:
                fecha_final = libro.get('fecha_devolucion', '')
                assert fecha_final == nueva_fecha, f"Fecha no actualizada correctamente: {fecha_final} != {nueva_fecha}"
                break
        
        print("Fecha de devolución actualizada correctamente")
        
        # Limpiar
        subscriber.detener()
        
        # Actualizar resultados
        self.resultados["operaciones_procesadas"] += 1
        self.resultados["tiempo_ack_promedio"] = (self.resultados["tiempo_ack_promedio"] + ack_ms) / 2
    
    def test_operacion_invalida(self):
        """Test de operación inválida - debe manejar error gracefully"""
        print("\nTest: Operación inválida")
        
        # Enviar operación inválida
        payload = {
            "op": "OPERACION_INVALIDA",
            "libro_id": "L999",
            "usuario_id": "U999"
        }
        
        print(f"Enviando operación inválida: {payload}")
        status, ack_ms = TestUtils.send_req(self.gc_endpoint, payload)
        
        # Debe responder con ERROR pero no crashear
        assert status == "ERROR", f"Debe responder ERROR para operación inválida, obtuvo: {status}"
        assert ack_ms < 500, f"ACK tardó {ack_ms}ms, debe ser < 500ms"
        
        print("Operación inválida manejada correctamente")
        
        # Actualizar resultados
        self.resultados["operaciones_procesadas"] += 1
    
    def teardown_method(self):
        """Limpieza después de cada test"""
        # Marcar test como pasado si llegamos hasta aquí
        self.resultados["passed"] = True
        
        # Generar reporte
        TestUtils.generar_reporte_test(
            "test_end_to_end",
            self.resultados,
            self.logs_path
        )
        
        print(f"\nTest completado:")
        print(f"   Operaciones procesadas: {self.resultados['operaciones_procesadas']}")
        print(f"   Tiempo ACK promedio: {self.resultados['tiempo_ack_promedio']:.2f}ms")
        print(f"   Estado: {'PASSED' if self.resultados['passed'] else 'FAILED'}")
        print(f"   Reporte: {self.logs_path}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
