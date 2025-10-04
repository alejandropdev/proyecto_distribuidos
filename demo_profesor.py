#!/usr/bin/env python3
"""
Sistema Distribuido de Biblioteca - Menú de Opciones
===================================================

Interfaz principal del sistema distribuido de biblioteca con menú
de opciones para configuración, operaciones y monitoreo.

Uso: python demo_profesor.py
"""

import os
import sys
import time
import subprocess
import threading
import signal
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import zmq
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich import box
except ImportError as e:
    print(f"Dependencias faltantes: {e}")
    print("Por favor instale: pip install -r requirements.txt")
    sys.exit(1)

app = typer.Typer(help="Sistema Distribuido de Biblioteca - Menú de Opciones")
console = Console()

class SistemaBiblioteca:
    """Sistema distribuido de biblioteca con menú de opciones"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        self.setup_directories()
    
    def setup_directories(self):
        """Crear directorios necesarios"""
        dirs = ['data/siteA', 'data/siteB', 'metrics', 'logs']
        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
    
    def mostrar_titulo(self):
        """Mostrar título del sistema"""
        console.print(Panel.fit(
            "[bold blue]Sistema Distribuido de Biblioteca[/bold blue]\n"
            "[dim]Menú de Opciones Principal[/dim]",
            border_style="blue"
        ))
    
    def mostrar_estado_sistema(self):
        """Mostrar estado actual del sistema"""
        table = Table(title="Estado del Sistema", box=box.ROUNDED)
        table.add_column("Componente", style="cyan")
        table.add_column("Estado", style="green")
        table.add_column("Puerto", style="yellow")
        
        # Verificar servicios Docker
        try:
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, 
                                  cwd=self.project_root)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]
                for line in lines:
                    if line.strip() and 'sitio' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            servicio = parts[0]
                            estado = parts[1]
                            puerto = "Múltiples" if "sitio" in servicio else "N/A"
                            table.add_row(servicio, estado, puerto)
        except:
            pass
        
        # Verificar procesos locales
        for name, process in self.processes.items():
            estado = "Ejecutándose" if process.poll() is None else "Detenido"
            puerto = self.obtener_puerto_servicio(name)
            table.add_row(name, estado, puerto)
        
        console.print(table)
    
    def obtener_puerto_servicio(self, servicio: str) -> str:
        """Obtener puerto de un servicio"""
        puertos = {
            "GC": "5555",
            "AP": "5557", 
            "GA-A": "5560",
            "GA-B": "5561",
            "AR": "N/A",
            "AD": "N/A"
        }
        return puertos.get(servicio, "N/A")
    
    def generar_datos_iniciales(self):
        """Generar datos iniciales (1000 libros, 200 préstamos)"""
        console.print("[yellow]Generando datos iniciales...[/yellow]")
        console.print("[dim]✓ 1000 libros en total[/dim]")
        console.print("[dim]✓ 200 libros ya prestados (50 en sitio A, 150 en sitio B)[/dim]")
        console.print("[dim]✓ Copias idénticas en ambas sedes[/dim]")
        
        # Generar datos para Sitio A
        cmd_a = [
            sys.executable, "tools/seed_data.py",
            "--data-dir", "./data/siteA",
            "--site", "A",
            "--books", "1000",
            "--loans", "50"
        ]
        
        # Generar datos para Sitio B
        cmd_b = [
            sys.executable, "tools/seed_data.py", 
            "--data-dir", "./data/siteB",
            "--site", "B",
            "--books", "1000",
            "--loans", "150"
        ]
        
        try:
            subprocess.run(cmd_a, check=True, cwd=self.project_root)
            subprocess.run(cmd_b, check=True, cwd=self.project_root)
            console.print("[green]✓ Datos iniciales generados correctamente[/green]")
            
            # Mostrar resumen
            self.mostrar_resumen_datos()
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error generando datos: {e}[/red]")
            return False
    
    def mostrar_resumen_datos(self):
        """Mostrar resumen de los datos generados"""
        try:
            # Leer datos del sitio A
            with open('data/siteA/books.json', 'r') as f:
                books_a = json.load(f)
            with open('data/siteA/loans.json', 'r') as f:
                loans_a = json.load(f)
            
            # Leer datos del sitio B
            with open('data/siteB/books.json', 'r') as f:
                books_b = json.load(f)
            with open('data/siteB/loans.json', 'r') as f:
                loans_b = json.load(f)
            
            table = Table(title="Resumen de Datos Generados", box=box.ROUNDED)
            table.add_column("Sitio", style="cyan")
            table.add_column("Total Libros", style="green")
            table.add_column("Disponibles", style="green")
            table.add_column("Prestados", style="yellow")
            
            table.add_row("Sitio A", str(len(books_a)), 
                         str(sum(1 for b in books_a if b['disponible'])),
                         str(len(loans_a)))
            table.add_row("Sitio B", str(len(books_b)), 
                         str(sum(1 for b in books_b if b['disponible'])),
                         str(len(loans_b)))
            table.add_row("TOTAL", str(len(books_a) + len(books_b)), 
                         str(sum(1 for b in books_a + books_b if b['disponible'])),
                         str(len(loans_a) + len(loans_b)))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error mostrando resumen: {e}[/red]")
    
    def iniciar_sistema_docker(self):
        """Iniciar sistema completo con Docker"""
        console.print("[yellow]Iniciando sistema distribuido...[/yellow]")
        console.print("[dim]✓ Sitio A: GC + Actores[/dim]")
        console.print("[dim]✓ Sitio B: GA + Replicación[/dim]")
        console.print("[dim]✓ Comunicación ZeroMQ entre sitios[/dim]")
        
        try:
            # Construir y iniciar contenedores
            subprocess.run(['docker-compose', 'up', '-d', '--build'], 
                         check=True, cwd=self.project_root)
            
            # Esperar a que los servicios estén listos
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Esperando servicios...", total=None)
                time.sleep(10)
            
            console.print("[green]✓ Sistema iniciado correctamente[/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error iniciando sistema: {e}[/red]")
            return False
    
    def detener_sistema(self):
        """Detener sistema completo"""
        console.print("[yellow]Deteniendo sistema...[/yellow]")
        
        try:
            subprocess.run(['docker-compose', 'down'], 
                         check=True, cwd=self.project_root)
            console.print("[green]✓ Sistema detenido[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error deteniendo sistema: {e}[/red]")
    
    def demostrar_operacion_renovar(self):
        """Demostrar operación RENOVAR"""
        console.print(Panel.fit(
            "[bold yellow]DEMOSTRACIÓN: Operación RENOVAR[/bold yellow]\n"
            "[dim]Flujo: PS → GC → AR → GA[/dim]\n"
            "[dim]Patrón: REQ/REP + PUB/SUB[/dim]",
            border_style="yellow"
        ))
        
        console.print("[cyan]1. PS envía solicitud de renovación a GC[/cyan]")
        console.print("[cyan]2. GC responde inmediatamente 'RECIBIDO'[/cyan]")
        console.print("[cyan]3. GC publica en tópico RENOVACION[/cyan]")
        console.print("[cyan]4. AR procesa la renovación[/cyan]")
        console.print("[cyan]5. GA actualiza la base de datos[/cyan]")
        
        # Ejecutar prueba
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            request = {
                'id': 'demo-renovar-1',
                'sedeId': 'A',
                'userId': 'u-demo-1',
                'op': 'RENOVAR',
                'libroCodigo': 'ISBN-0001',
                'timestamp': int(time.time() * 1000)
            }
            
            console.print(f"[yellow]Enviando solicitud:[/yellow] {request}")
            socket.send_json(request)
            response = socket.recv_json()
            console.print(f"[green]Respuesta recibida:[/green] {response}")
            
            socket.close()
            context.term()
            
            console.print("[green]✓ Operación RENOVAR completada exitosamente[/green]")
            
            # Guardar petición en archivo
            self.guardar_peticion("RENOVAR", "ISBN-0001", "u-demo-1")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error en operación RENOVAR: {e}[/red]")
            return False
    
    def demostrar_operacion_devolver(self):
        """Demostrar operación DEVOLVER"""
        console.print(Panel.fit(
            "[bold yellow]DEMOSTRACIÓN: Operación DEVOLVER[/bold yellow]\n"
            "[dim]Flujo: PS → GC → AD → GA[/dim]\n"
            "[dim]Patrón: REQ/REP + PUB/SUB[/dim]",
            border_style="yellow"
        ))
        
        console.print("[cyan]1. PS envía solicitud de devolución a GC[/cyan]")
        console.print("[cyan]2. GC responde inmediatamente 'RECIBIDO'[/cyan]")
        console.print("[cyan]3. GC publica en tópico DEVOLUCION[/cyan]")
        console.print("[cyan]4. AD procesa la devolución[/cyan]")
        console.print("[cyan]5. GA actualiza la base de datos[/cyan]")
        
        # Ejecutar prueba
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            request = {
                'id': 'demo-devolver-1',
                'sedeId': 'A',
                'userId': 'u-demo-1',
                'op': 'DEVOLVER',
                'libroCodigo': 'ISBN-0001',
                'timestamp': int(time.time() * 1000)
            }
            
            console.print(f"[yellow]Enviando solicitud:[/yellow] {request}")
            socket.send_json(request)
            response = socket.recv_json()
            console.print(f"[green]Respuesta recibida:[/green] {response}")
            
            socket.close()
            context.term()
            
            console.print("[green]✓ Operación DEVOLVER completada exitosamente[/green]")
            
            # Guardar petición en archivo
            self.guardar_peticion("DEVOLVER", "ISBN-0001", "u-demo-1")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error en operación DEVOLVER: {e}[/red]")
            return False
    
    def mostrar_archivo_peticiones(self):
        """Mostrar archivo de peticiones"""
        console.print(Panel.fit(
            "[bold cyan]ARCHIVO DE PETICIONES[/bold cyan]\n"
            "[dim]Formato: OPERACION CODIGO_LIBRO USUARIO[/dim]",
            border_style="cyan"
        ))
        
        try:
            with open('data/peticiones.txt', 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            console.print("[yellow]Contenido del archivo peticiones.txt:[/yellow]")
            
            if contenido.strip():
                console.print(f"[dim]{contenido}[/dim]")
                
                # Contar tipos de operaciones (solo líneas que no sean comentarios)
                lineas = [linea.strip() for linea in contenido.split('\n') if linea.strip() and not linea.strip().startswith('#')]
                renovar_count = sum(1 for linea in lineas if linea.startswith('RENOVAR'))
                devolver_count = sum(1 for linea in lineas if linea.startswith('DEVOLVER'))
                prestar_count = sum(1 for linea in lineas if linea.startswith('PRESTAR'))
                
                if renovar_count > 0 or devolver_count > 0 or prestar_count > 0:
                    table = Table(title="Resumen de Peticiones", box=box.ROUNDED)
                    table.add_column("Operación", style="cyan")
                    table.add_column("Cantidad", style="green")
                    
                    table.add_row("RENOVAR", str(renovar_count))
                    table.add_row("DEVOLVER", str(devolver_count))
                    table.add_row("PRESTAR", str(prestar_count))
                    table.add_row("TOTAL", str(len(lineas)))
                    
                    console.print(table)
                else:
                    console.print("[yellow]El archivo está vacío o solo contiene comentarios.[/yellow]")
                    console.print("[dim]Las peticiones se agregarán automáticamente cuando realice operaciones.[/dim]")
            else:
                console.print("[yellow]El archivo está vacío.[/yellow]")
                console.print("[dim]Las peticiones se agregarán automáticamente cuando realice operaciones.[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error leyendo archivo: {e}[/red]")
    
    def ejecutar_generacion_carga(self):
        """Ejecutar generación de carga automática"""
        console.print(Panel.fit(
            "[bold magenta]GENERACIÓN DE CARGA AUTOMÁTICA[/bold magenta]\n"
            "[dim]Múltiples PS leyendo desde archivo[/dim]",
            border_style="magenta"
        ))
        
        console.print("[cyan]✓ Lectura automática desde peticiones.txt[/cyan]")
        console.print("[cyan]✓ Múltiples procesos PS simultáneos[/cyan]")
        console.print("[cyan]✓ Comunicación distribuida entre máquinas[/cyan]")
        
        # Ejecutar generación de carga
        cmd = [
            sys.executable, "tools/spawn_ps.py",
            "--ps-per-site", "2",
            "--sites", "A,B",
            "--duration-sec", "30",
            "--file", "data/peticiones.txt",
            "--gc", "tcp://127.0.0.1:5555",
            "--mode", "serial",
            "--out", "metrics/results.csv"
        ]
        
        try:
            console.print("[yellow]Ejecutando generación de carga...[/yellow]")
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✓ Generación de carga completada[/green]")
                self.mostrar_resultados_carga()
                return True
            else:
                console.print(f"[red]Error en generación de carga: {result.stderr}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error ejecutando carga: {e}[/red]")
            return False
    
    def mostrar_resultados_carga(self):
        """Mostrar resultados de la generación de carga"""
        try:
            if os.path.exists('metrics/results.csv'):
                with open('metrics/results.csv', 'r') as f:
                    lineas = f.readlines()
                
                console.print("[green]✓ Resultados guardados en metrics/results.csv[/green]")
                console.print(f"[dim]Total de mediciones: {len(lineas)-1}[/dim]")
                
                if len(lineas) > 1:
                    # Mostrar primera línea de resultados
                    headers = lineas[0].strip().split(',')
                    valores = lineas[1].strip().split(',')
                    
                    table = Table(title="Métricas de Rendimiento", box=box.ROUNDED)
                    for header, valor in zip(headers, valores):
                        table.add_row(header, valor)
                    
                    console.print(table)
        except Exception as e:
            console.print(f"[red]Error mostrando resultados: {e}[/red]")
    
    def mostrar_logs_tiempo_real(self):
        """Mostrar logs en tiempo real"""
        console.print(Panel.fit(
            "[bold red]LOGS EN TIEMPO REAL[/bold red]\n"
            "[dim]Mostrando comunicación entre componentes[/dim]",
            border_style="red"
        ))
        
        console.print("[yellow]Presione Ctrl+C para detener la visualización[/yellow]")
        
        try:
            subprocess.run(['docker-compose', 'logs', '-f'], 
                         cwd=self.project_root)
        except KeyboardInterrupt:
            console.print("\n[yellow]Visualización de logs detenida[/yellow]")
    
    def mostrar_estado_final_bd(self):
        """Mostrar estado final de la base de datos"""
        console.print(Panel.fit(
            "[bold green]ESTADO FINAL DE LA BASE DE DATOS[/bold green]\n"
            "[dim]Después de ejecutar las operaciones[/dim]",
            border_style="green"
        ))
        
        try:
            # Mostrar algunos libros y préstamos actualizados
            with open('data/siteA/books.json', 'r') as f:
                books = json.load(f)
            with open('data/siteA/loans.json', 'r') as f:
                loans = json.load(f)
            
            console.print("[cyan]Libros en Sitio A:[/cyan]")
            table_books = Table(title="Muestra de Libros", box=box.ROUNDED)
            table_books.add_column("Código", style="cyan")
            table_books.add_column("Título", style="green")
            table_books.add_column("Disponible", style="yellow")
            
            for book in books[:5]:
                table_books.add_row(
                    book['codigo'],
                    book['titulo'][:30] + "...",
                    "Sí" if book['disponible'] else "No"
                )
            
            console.print(table_books)
            
            console.print("\n[cyan]Préstamos en Sitio A:[/cyan]")
            table_loans = Table(title="Muestra de Préstamos", box=box.ROUNDED)
            table_loans.add_column("Código", style="cyan")
            table_loans.add_column("Usuario", style="green")
            table_loans.add_column("Fecha Vencimiento", style="yellow")
            table_loans.add_column("Renovaciones", style="magenta")
            
            for loan in loans[:5]:
                table_loans.add_row(
                    loan['codigo'],
                    loan['userId'],
                    loan['dueDate'],
                    str(loan['renovaciones'])
                )
            
            console.print(table_loans)
            
        except Exception as e:
            console.print(f"[red]Error mostrando estado final: {e}[/red]")
    
    def guardar_peticion(self, operacion: str, codigo_libro: str, usuario: str):
        """Guardar petición en el archivo peticiones.txt"""
        try:
            peticion_linea = f"{operacion} {codigo_libro} {usuario}\n"
            with open('data/peticiones.txt', 'a', encoding='utf-8') as f:
                f.write(peticion_linea)
            console.print(f"[dim]Petición guardada: {peticion_linea.strip()}[/dim]")
        except Exception as e:
            console.print(f"[red]Error guardando petición: {e}[/red]")
    
    def operacion_manual(self):
        """Permitir operaciones manuales interactivas"""
        console.print(Panel.fit(
            "[bold green]OPERACIONES MANUALES[/bold green]\n"
            "[dim]Seleccione libros y operaciones interactivamente[/dim]",
            border_style="green"
        ))
        
        try:
            # Cargar libros disponibles
            with open('data/siteA/books.json', 'r') as f:
                books = json.load(f)
            
            # Mostrar algunos libros disponibles
            libros_disponibles = [book for book in books if book['disponible']][:10]
            
            console.print("[cyan]Libros disponibles (primeros 10):[/cyan]")
            table = Table(title="Libros Disponibles", box=box.ROUNDED)
            table.add_column("Número", style="cyan")
            table.add_column("Código", style="green")
            table.add_column("Título", style="yellow")
            
            for i, book in enumerate(libros_disponibles, 1):
                table.add_row(str(i), book['codigo'], book['titulo'][:40] + "...")
            
            console.print(table)
            
            # Seleccionar operación
            console.print("\n[yellow]Tipos de operación disponibles:[/yellow]")
            console.print("1. RENOVAR - Renovar préstamo existente")
            console.print("2. DEVOLVER - Devolver libro prestado")
            console.print("3. PRESTAR - Prestar libro disponible")
            
            opcion = Prompt.ask("Seleccione tipo de operación", choices=["1", "2", "3"])
            
            operaciones = {"1": "RENOVAR", "2": "DEVOLVER", "3": "PRESTAR"}
            operacion = operaciones[opcion]
            
            # Seleccionar libro
            libro_num = int(Prompt.ask("Seleccione número de libro (1-10)"))
            if 1 <= libro_num <= len(libros_disponibles):
                libro = libros_disponibles[libro_num - 1]
                codigo_libro = libro['codigo']
            else:
                console.print("[red]Número de libro inválido[/red]")
                return False
            
            # Ingresar usuario
            usuario = Prompt.ask("Ingrese ID de usuario (ej: u-123)")
            
            # Ejecutar operación
            console.print(f"[yellow]Ejecutando operación {operacion} para libro {codigo_libro} y usuario {usuario}...[/yellow]")
            
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            request = {
                'id': f'manual-{int(time.time())}',
                'sedeId': 'A',
                'userId': usuario,
                'op': operacion,
                'libroCodigo': codigo_libro,
                'timestamp': int(time.time() * 1000)
            }
            
            console.print(f"[yellow]Enviando solicitud:[/yellow] {request}")
            socket.send_json(request)
            response = socket.recv_json()
            console.print(f"[green]Respuesta recibida:[/green] {response}")
            
            socket.close()
            context.term()
            
            console.print(f"[green]✓ Operación {operacion} completada exitosamente[/green]")
            
            # Guardar petición en archivo
            self.guardar_peticion(operacion, codigo_libro, usuario)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error en operación manual: {e}[/red]")
            return False

# Instancia global del sistema
sistema = SistemaBiblioteca()

def signal_handler(signum, frame):
    """Manejar Ctrl+C graciosamente"""
    console.print("\n[yellow]Cerrando sistema...[/yellow]")
    sistema.detener_sistema()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

@app.command()
def main():
    """Menú principal del sistema de biblioteca"""
    
    sistema.mostrar_titulo()
    
    while True:
        console.print("\n" + "="*60)
        console.print("[bold cyan]MENÚ DE OPCIONES DEL SISTEMA[/bold cyan]")
        console.print("="*60)
        
        # Mostrar estado del sistema
        sistema.mostrar_estado_sistema()
        
        console.print("\n[bold yellow]OPCIONES DISPONIBLES:[/bold yellow]")
        console.print("1. [green]Configurar Datos Iniciales[/green] - Generar 1000 libros, 200 préstamos")
        console.print("2. [blue]Iniciar Sistema Distribuido[/blue] - Activar todos los componentes")
        console.print("3. [yellow]Demostrar RENOVAR[/yellow] - Operación de renovación")
        console.print("4. [yellow]Demostrar DEVOLVER[/yellow] - Operación de devolución")
        console.print("5. [green]Operaciones Manuales[/green] - Seleccionar libros y operaciones")
        console.print("6. [cyan]Mostrar Archivo Peticiones[/cyan] - Formato de carga automática")
        console.print("7. [magenta]Ejecutar Generación de Carga[/magenta] - Múltiples PS automáticos")
        console.print("8. [red]Ver Logs en Tiempo Real[/red] - Comunicación entre componentes")
        console.print("9. [green]Mostrar Estado Final BD[/green] - Resultados de las operaciones")
        console.print("10. [orange]Detener Sistema[/orange] - Cerrar todos los componentes")
        console.print("11. [dim]Salir[/dim] - Terminar sistema")
        
        choice = Prompt.ask("\nSeleccione una opción", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])
        
        if choice == "1":
            sistema.generar_datos_iniciales()
            
        elif choice == "2":
            if Confirm.ask("¿Iniciar sistema distribuido?"):
                sistema.iniciar_sistema_docker()
                
        elif choice == "3":
            sistema.demostrar_operacion_renovar()
            
        elif choice == "4":
            sistema.demostrar_operacion_devolver()
            
        elif choice == "5":
            sistema.operacion_manual()
            
        elif choice == "6":
            sistema.mostrar_archivo_peticiones()
            
        elif choice == "7":
            if Confirm.ask("¿Ejecutar generación de carga?"):
                sistema.ejecutar_generacion_carga()
                
        elif choice == "8":
            sistema.mostrar_logs_tiempo_real()
            
        elif choice == "9":
            sistema.mostrar_estado_final_bd()
            
        elif choice == "10":
            if Confirm.ask("¿Detener sistema?"):
                sistema.detener_sistema()
                
        elif choice == "11":
            if Confirm.ask("¿Terminar sistema?"):
                sistema.detener_sistema()
                console.print("[green]¡Sistema cerrado correctamente![/green]")
                break

if __name__ == "__main__":
    app()
