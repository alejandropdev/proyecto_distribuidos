#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba del Sistema Distribuido
Verifica que el sistema funciona correctamente con los datos iniciales
"""

import json
import os
import subprocess
import time
import signal
import sys
from datetime import datetime

def verificar_estructura_datos():
    """Verifica que la estructura de datos es correcta"""
    print("🔍 Verificando estructura de datos...")
    
    try:
        with open('data/libros.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Verificar metadata
        metadata = datos.get('metadata', {})
        print(f"  ✅ Total libros: {metadata.get('total_libros', 0)}")
        print(f"  ✅ Total ejemplares: {metadata.get('total_ejemplares', 0)}")
        print(f"  ✅ Ejemplares disponibles: {metadata.get('ejemplares_disponibles', 0)}")
        print(f"  ✅ Ejemplares prestados SEDE_1: {metadata.get('ejemplares_prestados_sede_1', 0)}")
        print(f"  ✅ Ejemplares prestados SEDE_2: {metadata.get('ejemplares_prestados_sede_2', 0)}")
        
        # Verificar que tenemos exactamente 1000 libros
        libros = datos.get('libros', [])
        if len(libros) != 1000:
            print(f"  ❌ Error: Se esperaban 1000 libros, se encontraron {len(libros)}")
            return False
        
        # Verificar que tenemos 200 ejemplares prestados
        total_prestados = metadata.get('ejemplares_prestados_sede_1', 0) + metadata.get('ejemplares_prestados_sede_2', 0)
        if total_prestados != 200:
            print(f"  ❌ Error: Se esperaban 200 ejemplares prestados, se encontraron {total_prestados}")
            return False
        
        # Verificar distribución por sedes
        if metadata.get('ejemplares_prestados_sede_1', 0) != 50:
            print(f"  ❌ Error: Se esperaban 50 ejemplares prestados en SEDE_1")
            return False
        
        if metadata.get('ejemplares_prestados_sede_2', 0) != 150:
            print(f"  ❌ Error: Se esperaban 150 ejemplares prestados en SEDE_2")
            return False
        
        print("  ✅ Estructura de datos verificada correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ Error verificando datos: {e}")
        return False

def verificar_archivo_solicitudes():
    """Verifica que el archivo de solicitudes existe y tiene formato correcto"""
    print("🔍 Verificando archivo de solicitudes...")
    
    try:
        if not os.path.exists('data/solicitudes.txt'):
            print("  ❌ Archivo de solicitudes no encontrado")
            return False
        
        with open('data/solicitudes.txt', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        solicitudes_validas = 0
        for i, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                partes = linea.split()
                if len(partes) >= 4:
                    operacion, libro_id, usuario_id, sede = partes[:4]
                    if operacion in ['RENOVACION', 'DEVOLUCION'] and sede in ['SEDE_1', 'SEDE_2']:
                        solicitudes_validas += 1
                    else:
                        print(f"  ⚠️  Línea {i} con formato incorrecto: {linea}")
                else:
                    print(f"  ⚠️  Línea {i} incompleta: {linea}")
        
        print(f"  ✅ {solicitudes_validas} solicitudes válidas encontradas")
        return solicitudes_validas > 0
        
    except Exception as e:
        print(f"  ❌ Error verificando solicitudes: {e}")
        return False

def verificar_scripts():
    """Verifica que todos los scripts principales existen"""
    print("🔍 Verificando scripts del sistema...")
    
    scripts = [
        'gestor_carga.py',
        'proceso_solicitante.py', 
        'actor_devolucion.py',
        'actor_renovacion.py',
        'generar_datos_iniciales.py'
    ]
    
    todos_existen = True
    for script in scripts:
        if os.path.exists(script):
            print(f"  ✅ {script}")
        else:
            print(f"  ❌ {script} no encontrado")
            todos_existen = False
    
    return todos_existen

def mostrar_estadisticas_iniciales():
    """Muestra estadísticas de los datos iniciales"""
    print("\n📊 ESTADÍSTICAS DE DATOS INICIALES")
    print("="*50)
    
    try:
        with open('data/libros.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        metadata = datos.get('metadata', {})
        libros = datos.get('libros', [])
        
        # Estadísticas generales
        print(f"Total de libros: {metadata.get('total_libros', 0)}")
        print(f"Total de ejemplares: {metadata.get('total_ejemplares', 0)}")
        print(f"Ejemplares disponibles: {metadata.get('ejemplares_disponibles', 0)}")
        print(f"Ejemplares prestados: {metadata.get('ejemplares_prestados_sede_1', 0) + metadata.get('ejemplares_prestados_sede_2', 0)}")
        
        # Estadísticas por sede
        print(f"\nPor sede:")
        print(f"  SEDE_1: {metadata.get('ejemplares_prestados_sede_1', 0)} ejemplares prestados")
        print(f"  SEDE_2: {metadata.get('ejemplares_prestados_sede_2', 0)} ejemplares prestados")
        
        # Estadísticas de libros
        libros_con_1_ejemplar = sum(1 for libro in libros if libro.get('total_ejemplares', 0) == 1)
        libros_con_multiples = sum(1 for libro in libros if libro.get('total_ejemplares', 0) > 1)
        
        print(f"\nDistribución de libros:")
        print(f"  Libros con 1 ejemplar: {libros_con_1_ejemplar}")
        print(f"  Libros con múltiples ejemplares: {libros_con_multiples}")
        
        # Ejemplos de libros prestados
        print(f"\nEjemplos de libros con ejemplares prestados:")
        contador = 0
        for libro in libros:
            if libro.get('ejemplares_prestados', 0) > 0 and contador < 5:
                print(f"  {libro.get('libro_id', 'N/A')}: {libro.get('titulo', 'N/A')} - {libro.get('ejemplares_prestados', 0)} prestados")
                contador += 1
        
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error mostrando estadísticas: {e}")

def main():
    """Función principal de verificación"""
    print("🚀 VERIFICACIÓN DEL SISTEMA DISTRIBUIDO")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cambiar al directorio del sistema
    os.chdir('/Users/alejoparrado/Desktop/proyecto_distribuidos/sistema_distribuido')
    
    # Verificaciones
    verificaciones = [
        ("Estructura de datos", verificar_estructura_datos),
        ("Archivo de solicitudes", verificar_archivo_solicitudes),
        ("Scripts del sistema", verificar_scripts)
    ]
    
    todas_pasaron = True
    for nombre, funcion in verificaciones:
        print(f"\n{nombre}:")
        if not funcion():
            todas_pasaron = False
    
    # Mostrar estadísticas
    mostrar_estadisticas_iniciales()
    
    # Resultado final
    print(f"\n{'='*60}")
    if todas_pasaron:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("🎉 El sistema está listo para funcionar!")
        print("\nPara probar el sistema:")
        print("1. Ejecutar: docker-compose up -d")
        print("2. Verificar logs: docker-compose logs -f")
        print("3. Ejecutar solicitudes: ./demo_interactivo.sh")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("🔧 Revisar los errores antes de continuar")
    
    print("="*60)

if __name__ == "__main__":
    main()
