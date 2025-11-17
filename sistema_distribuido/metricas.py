#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Métricas - Sistema Distribuido de Préstamo de Libros
Registra tiempos de respuesta, desviación estándar y estadísticas de préstamos
"""

import time
import csv
import os
import statistics
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class Metricas:
    """Gestiona las métricas del sistema"""
    
    def __init__(self, archivo_csv="logs/metricas.csv"):
        """
        Inicializa el sistema de métricas
        
        Args:
            archivo_csv: Ruta al archivo CSV donde se guardan las métricas
        """
        self.archivo_csv = archivo_csv
        self.tiempos_respuesta: List[float] = []
        self.inicio_periodo: Optional[float] = None
        self.periodo_duracion = 120  # 2 minutos en segundos
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(archivo_csv), exist_ok=True)
        
        # Inicializar archivo CSV si no existe
        self._inicializar_csv()
    
    def _inicializar_csv(self):
        """Inicializa el archivo CSV con los encabezados"""
        if not os.path.exists(self.archivo_csv):
            with open(self.archivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'operacion',
                    'tiempo_respuesta_ms',
                    'libro_id',
                    'exito',
                    'total_prestamos_2min',
                    'tiempo_promedio_ms',
                    'desviacion_estandar_ms'
                ])
    
    def registrar_prestamo(self, tiempo_respuesta_ms: float, libro_id: str, exito: bool):
        """
        Registra una operación de préstamo
        
        Args:
            tiempo_respuesta_ms: Tiempo de respuesta en milisegundos
            libro_id: ID del libro
            exito: True si la operación fue exitosa
        """
        timestamp = datetime.now().isoformat()
        
        # Iniciar período si es el primer préstamo
        if self.inicio_periodo is None:
            self.inicio_periodo = time.time()
        
        # Agregar tiempo de respuesta
        self.tiempos_respuesta.append(tiempo_respuesta_ms)
        
        # Calcular estadísticas del período actual (últimos 2 minutos)
        tiempo_actual = time.time()
        if tiempo_actual - self.inicio_periodo > self.periodo_duracion:
            # Reiniciar período
            self.tiempos_respuesta = [tiempo_respuesta_ms]
            self.inicio_periodo = tiempo_actual
        
        # Calcular estadísticas
        total_prestamos_2min = len(self.tiempos_respuesta)
        tiempo_promedio_ms = statistics.mean(self.tiempos_respuesta) if self.tiempos_respuesta else 0.0
        
        try:
            desviacion_estandar_ms = statistics.stdev(self.tiempos_respuesta) if len(self.tiempos_respuesta) > 1 else 0.0
        except statistics.StatisticsError:
            desviacion_estandar_ms = 0.0
        
        # Escribir en CSV
        try:
            with open(self.archivo_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    'PRESTAMO',
                    f"{tiempo_respuesta_ms:.2f}",
                    libro_id,
                    'SI' if exito else 'NO',
                    total_prestamos_2min,
                    f"{tiempo_promedio_ms:.2f}",
                    f"{desviacion_estandar_ms:.2f}"
                ])
        except Exception as e:
            logger.error(f"Error escribiendo métricas a CSV: {e}")
        
        logger.debug(f"Métrica registrada: {tiempo_respuesta_ms:.2f}ms, Préstamos en 2min: {total_prestamos_2min}, Promedio: {tiempo_promedio_ms:.2f}ms, DesvEst: {desviacion_estandar_ms:.2f}ms")
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene las estadísticas actuales
        
        Returns:
            Dict con estadísticas: total_prestamos, tiempo_promedio_ms, desviacion_estandar_ms, prestamos_2min
        """
        total_prestamos = len(self.tiempos_respuesta)
        
        if total_prestamos == 0:
            return {
                "total_prestamos": 0,
                "tiempo_promedio_ms": 0.0,
                "desviacion_estandar_ms": 0.0,
                "prestamos_2min": 0
            }
        
        tiempo_promedio_ms = statistics.mean(self.tiempos_respuesta)
        
        try:
            desviacion_estandar_ms = statistics.stdev(self.tiempos_respuesta) if total_prestamos > 1 else 0.0
        except statistics.StatisticsError:
            desviacion_estandar_ms = 0.0
        
        # Contar préstamos en los últimos 2 minutos
        tiempo_actual = time.time()
        if self.inicio_periodo and (tiempo_actual - self.inicio_periodo) <= self.periodo_duracion:
            prestamos_2min = total_prestamos
        else:
            prestamos_2min = 0
        
        return {
            "total_prestamos": total_prestamos,
            "tiempo_promedio_ms": tiempo_promedio_ms,
            "desviacion_estandar_ms": desviacion_estandar_ms,
            "prestamos_2min": prestamos_2min
        }
    
    def mostrar_estadisticas(self):
        """Muestra las estadísticas en consola"""
        stats = self.obtener_estadisticas()
        
        print("\n" + "="*60)
        print("ESTADÍSTICAS DE PRÉSTAMOS")
        print("="*60)
        print(f"Total de préstamos procesados: {stats['total_prestamos']}")
        print(f"Préstamos en últimos 2 minutos: {stats['prestamos_2min']}")
        print(f"Tiempo promedio de respuesta: {stats['tiempo_promedio_ms']:.2f} ms")
        print(f"Desviación estándar: {stats['desviacion_estandar_ms']:.2f} ms")
        print("="*60 + "\n")

def obtener_timestamp_ms() -> float:
    """
    Obtiene el timestamp actual en milisegundos
    
    Returns:
        Timestamp en milisegundos
    """
    return time.time() * 1000

def medir_tiempo_respuesta(inicio_ms: float, fin_ms: float) -> float:
    """
    Calcula el tiempo de respuesta entre dos timestamps
    
    Args:
        inicio_ms: Timestamp de inicio en milisegundos
        fin_ms: Timestamp de fin en milisegundos
    
    Returns:
        Tiempo de respuesta en milisegundos
    """
    return fin_ms - inicio_ms

