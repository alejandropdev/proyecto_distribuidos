#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Experimentos de Rendimiento - Sistema Distribuido de Préstamo de Libros
Ejecuta experimentos comparando modo serial vs multihilos con diferentes configuraciones de PS
"""

import os
import sys
import subprocess
import time
import csv
import json
import statistics
from datetime import datetime
from pathlib import Path

# Configuración de experimentos
EXPERIMENTOS = [
    {"modo": "serial", "ps_sede_1": 2, "ps_sede_2": 2, "duracion_min": 2},
    {"modo": "serial", "ps_sede_1": 3, "ps_sede_2": 3, "duracion_min": 2},
    {"modo": "serial", "ps_sede_1": 5, "ps_sede_2": 5, "duracion_min": 2},
    {"modo": "multithread", "ps_sede_1": 2, "ps_sede_2": 2, "duracion_min": 2, "workers": 4},
    {"modo": "multithread", "ps_sede_1": 3, "ps_sede_2": 3, "duracion_min": 2, "workers": 4},
    {"modo": "multithread", "ps_sede_1": 5, "ps_sede_2": 5, "duracion_min": 2, "workers": 4},
]

def ejecutar_comando(comando, cwd=None):
    """Ejecuta un comando y retorna el resultado"""
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return resultado.returncode == 0, resultado.stdout, resultado.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout ejecutando comando"
    except Exception as e:
        return False, "", str(e)

def generar_solicitudes(num_solicitudes, archivo_salida):
    """Genera un archivo de solicitudes de préstamo"""
    solicitudes = []
    for i in range(num_solicitudes):
        libro_id = f"L{((i % 1000) + 1):04d}"  # Ciclar entre L0001 y L1000
        usuario_id = f"U{(i % 1000) + 1:04d}"
        sede = "SEDE_1" if i % 2 == 0 else "SEDE_2"
        solicitudes.append(f"PRESTAMO {libro_id} {usuario_id} {sede}")
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write('\n'.join(solicitudes))
    
    print(f"✅ Generadas {num_solicitudes} solicitudes en {archivo_salida}")

def levantar_servicios(modo="serial", workers=4):
    """Levanta los servicios principales del sistema"""
    print(f"\n🔧 Levantando servicios en modo {modo}...")
    
    # Detener servicios existentes
    ejecutar_comando("docker compose down", cwd="sistema_distribuido")
    
    # Configurar variables de entorno
    env_vars = {
        "GC_MODE": modo,
        "GC_WORKERS": str(workers) if modo == "multithread" else "1"
    }
    
    # Construir comando
    env_str = " ".join([f"{k}={v}" for k, v in env_vars.items()])
    comando = f"{env_str} docker compose up --build -d ga gc actor_prestamo"
    
    exito, stdout, stderr = ejecutar_comando(comando, cwd="sistema_distribuido")
    
    if not exito:
        print(f"❌ Error levantando servicios: {stderr}")
        return False
    
    # Esperar a que los servicios estén listos
    print("⏳ Esperando a que los servicios estén listos...")
    time.sleep(10)
    
    # Verificar que los servicios estén corriendo
    exito, stdout, stderr = ejecutar_comando("docker compose ps", cwd="sistema_distribuido")
    if "ga" in stdout and "gc" in stdout and "actor_prestamo" in stdout:
        print("✅ Servicios levantados correctamente")
        return True
    else:
        print(f"❌ Algunos servicios no están corriendo: {stdout}")
        return False

def ejecutar_ps(archivo_solicitudes, sede, num_instancias=1):
    """Ejecuta instancias de PS en paralelo"""
    procesos = []
    
    for i in range(num_instancias):
        # Crear archivo de solicitudes único para esta instancia
        archivo_instancia = f"{archivo_solicitudes}.{sede}.{i}.txt"
        if not os.path.exists(archivo_instancia):
            # Copiar archivo base y modificar sede si es necesario
            with open(archivo_solicitudes, 'r') as f:
                lineas = f.readlines()
            
            lineas_modificadas = []
            for linea in lineas:
                partes = linea.strip().split()
                if len(partes) >= 4:
                    partes[3] = sede  # Cambiar sede
                lineas_modificadas.append(' '.join(partes))
            
            with open(archivo_instancia, 'w') as f:
                f.write('\n'.join(lineas_modificadas))
        
        # Ejecutar PS en background
        comando = f"docker compose run --rm -e GC_HOST=gc -e GC_PORT=5001 ps python proceso_solicitante.py {archivo_instancia}"
        proceso = subprocess.Popen(
            comando,
            shell=True,
            cwd="sistema_distribuido",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        procesos.append((proceso, archivo_instancia))
    
    return procesos

def esperar_procesos(procesos, timeout_seconds=180):
    """Espera a que los procesos terminen"""
    inicio = time.time()
    
    while time.time() - inicio < timeout_seconds:
        todos_terminados = True
        for proceso, archivo in procesos:
            if proceso.poll() is None:
                todos_terminados = False
                break
        
        if todos_terminados:
            break
        
        time.sleep(1)
    
    # Terminar procesos que aún estén corriendo
    for proceso, archivo in procesos:
        if proceso.poll() is None:
            proceso.terminate()
            proceso.wait(timeout=5)

def analizar_metricas(archivo_csv="sistema_distribuido/logs/metricas.csv"):
    """Analiza las métricas del experimento"""
    if not os.path.exists(archivo_csv):
        return {
            "total_prestamos": 0,
            "tiempo_promedio_ms": 0.0,
            "desviacion_estandar_ms": 0.0,
            "prestamos_2min": 0
        }
    
    tiempos = []
    prestamos_2min = 0
    
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('operacion') == 'PRESTAMO':
                tiempo = float(row.get('tiempo_respuesta_ms', 0))
                tiempos.append(tiempo)
                
                # Contar préstamos en últimos 2 minutos
                total_2min = int(row.get('total_prestamos_2min', 0))
                if total_2min > prestamos_2min:
                    prestamos_2min = total_2min
    
    if not tiempos:
        return {
            "total_prestamos": 0,
            "tiempo_promedio_ms": 0.0,
            "desviacion_estandar_ms": 0.0,
            "prestamos_2min": 0
        }
    
    tiempo_promedio = statistics.mean(tiempos)
    desviacion_estandar = statistics.stdev(tiempos) if len(tiempos) > 1 else 0.0
    
    return {
        "total_prestamos": len(tiempos),
        "tiempo_promedio_ms": tiempo_promedio,
        "desviacion_estandar_ms": desviacion_estandar,
        "prestamos_2min": prestamos_2min
    }

def ejecutar_experimento(experimento):
    """Ejecuta un experimento completo"""
    modo = experimento["modo"]
    ps_sede_1 = experimento["ps_sede_1"]
    ps_sede_2 = experimento["ps_sede_2"]
    duracion_min = experimento.get("duracion_min", 2)
    workers = experimento.get("workers", 4)
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENTO: Modo {modo.upper()}")
    print(f"  PS SEDE_1: {ps_sede_1}")
    print(f"  PS SEDE_2: {ps_sede_2}")
    print(f"  Workers: {workers if modo == 'multithread' else 1}")
    print(f"  Duración: {duracion_min} minutos")
    print(f"{'='*60}")
    
    # Generar archivo de solicitudes (suficientes para 2 minutos)
    num_solicitudes = (ps_sede_1 + ps_sede_2) * 60 * duracion_min  # ~1 solicitud por segundo por PS
    archivo_solicitudes = "sistema_distribuido/data/solicitudes_experimento.txt"
    generar_solicitudes(num_solicitudes, archivo_solicitudes)
    
    # Levantar servicios
    if not levantar_servicios(modo, workers):
        return None
    
    # Limpiar métricas anteriores
    archivo_metricas = "sistema_distribuido/logs/metricas.csv"
    if os.path.exists(archivo_metricas):
        os.remove(archivo_metricas)
    
    # Inicializar CSV de métricas
    os.makedirs(os.path.dirname(archivo_metricas), exist_ok=True)
    with open(archivo_metricas, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'operacion', 'tiempo_respuesta_ms', 'libro_id',
            'exito', 'total_prestamos_2min', 'tiempo_promedio_ms', 'desviacion_estandar_ms'
        ])
    
    # Ejecutar PS en paralelo
    print(f"\n🚀 Iniciando {ps_sede_1 + ps_sede_2} instancias de PS...")
    procesos = []
    
    procesos.extend(ejecutar_ps(archivo_solicitudes, "SEDE_1", ps_sede_1))
    procesos.extend(ejecutar_ps(archivo_solicitudes, "SEDE_2", ps_sede_2))
    
    # Esperar duración del experimento
    print(f"⏳ Ejecutando experimento por {duracion_min} minutos...")
    time.sleep(duracion_min * 60)
    
    # Terminar procesos
    print("🛑 Deteniendo procesos PS...")
    esperar_procesos(procesos, timeout_seconds=30)
    
    # Esperar un poco más para que se registren todas las métricas
    time.sleep(5)
    
    # Analizar métricas
    print("\n📊 Analizando métricas...")
    metricas = analizar_metricas(archivo_metricas)
    
    resultado = {
        "modo": modo,
        "ps_sede_1": ps_sede_1,
        "ps_sede_2": ps_sede_2,
        "workers": workers if modo == "multithread" else 1,
        "duracion_min": duracion_min,
        "timestamp": datetime.now().isoformat(),
        **metricas
    }
    
    print(f"\n✅ Experimento completado:")
    print(f"  Total préstamos: {resultado['total_prestamos']}")
    print(f"  Tiempo promedio: {resultado['tiempo_promedio_ms']:.2f} ms")
    print(f"  Desviación estándar: {resultado['desviacion_estandar_ms']:.2f} ms")
    print(f"  Préstamos en 2min: {resultado['prestamos_2min']}")
    
    return resultado

def generar_reporte(resultados, archivo_salida="sistema_distribuido/logs/reporte_rendimiento.md"):
    """Genera un reporte en Markdown con los resultados"""
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write("# Reporte de Rendimiento - Sistema Distribuido de Préstamo de Libros\n\n")
        f.write(f"**Fecha de ejecución**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Resumen de Experimentos\n\n")
        f.write("| Modo | PS SEDE_1 | PS SEDE_2 | Workers | Total Préstamos | Tiempo Promedio (ms) | Desv. Est. (ms) | Préstamos 2min |\n")
        f.write("|------|-----------|-----------|---------|-----------------|----------------------|-----------------|----------------|\n")
        
        for resultado in resultados:
            if resultado:
                f.write(f"| {resultado['modo']} | {resultado['ps_sede_1']} | {resultado['ps_sede_2']} | "
                       f"{resultado['workers']} | {resultado['total_prestamos']} | "
                       f"{resultado['tiempo_promedio_ms']:.2f} | {resultado['desviacion_estandar_ms']:.2f} | "
                       f"{resultado['prestamos_2min']} |\n")
        
        f.write("\n## Análisis Comparativo\n\n")
        
        # Comparar serial vs multithread para misma configuración de PS
        f.write("### Comparación Serial vs Multithread\n\n")
        f.write("| Configuración PS | Modo | Tiempo Promedio (ms) | Throughput (préstamos/2min) |\n")
        f.write("|------------------|------|----------------------|------------------------------|\n")
        
        configs = {}
        for resultado in resultados:
            if resultado:
                key = f"{resultado['ps_sede_1']}+{resultado['ps_sede_2']}"
                if key not in configs:
                    configs[key] = {}
                configs[key][resultado['modo']] = resultado
        
        for config, modos in configs.items():
            for modo in ['serial', 'multithread']:
                if modo in modos:
                    r = modos[modo]
                    f.write(f"| {config} | {modo} | {r['tiempo_promedio_ms']:.2f} | {r['prestamos_2min']} |\n")
    
    print(f"\n✅ Reporte generado: {archivo_salida}")

def main():
    """Función principal"""
    print("="*60)
    print("EXPERIMENTOS DE RENDIMIENTO")
    print("Sistema Distribuido de Préstamo de Libros")
    print("="*60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("sistema_distribuido"):
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    resultados = []
    
    for i, experimento in enumerate(EXPERIMENTOS, 1):
        print(f"\n{'#'*60}")
        print(f"EXPERIMENTO {i}/{len(EXPERIMENTOS)}")
        print(f"{'#'*60}")
        
        resultado = ejecutar_experimento(experimento)
        if resultado:
            resultados.append(resultado)
        
        # Pausa entre experimentos
        if i < len(EXPERIMENTOS):
            print("\n⏸️  Pausa de 10 segundos antes del siguiente experimento...")
            time.sleep(10)
    
    # Generar reporte
    if resultados:
        generar_reporte(resultados)
        
        # Guardar resultados en JSON también
        archivo_json = "sistema_distribuido/logs/resultados_experimentos.json"
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        print(f"✅ Resultados guardados en JSON: {archivo_json}")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS EXPERIMENTOS COMPLETADOS")
    print("="*60)

if __name__ == "__main__":
    main()

