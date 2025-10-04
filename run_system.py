#!/usr/bin/env python3
"""
Distributed Library System - Main Menu Interface
===============================================

This script provides a user-friendly menu interface to run and monitor
the distributed library system without needing to execute commands manually.

Usage: python run_system.py
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
    print(f"Missing required dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

app = typer.Typer(help="Distributed Library System - Main Interface")
console = Console()

class SystemManager:
    """Manages the distributed library system components"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = ['data/siteA', 'data/siteB', 'metrics', 'logs']
        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        try:
            import zmq
            import pydantic
            import rich
            import typer
            return True
        except ImportError as e:
            console.print(f"[red]Missing dependency: {e}[/red]")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def generate_sample_data(self):
        """Generate sample data for both sites"""
        console.print("[yellow]Generating sample data...[/yellow]")
        
        # Generate data for Site A
        cmd_a = [
            sys.executable, "tools/seed_data.py",
            "--data-dir", "./data/siteA",
            "--site", "A"
        ]
        
        # Generate data for Site B
        cmd_b = [
            sys.executable, "tools/seed_data.py", 
            "--data-dir", "./data/siteB",
            "--site", "B"
        ]
        
        try:
            subprocess.run(cmd_a, check=True, cwd=self.project_root)
            subprocess.run(cmd_b, check=True, cwd=self.project_root)
            console.print("[green]✓ Sample data generated successfully[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error generating data: {e}[/red]")
            return False
        return True
    
    def start_docker_system(self):
        """Start the system using Docker"""
        console.print("[yellow]Starting Docker system...[/yellow]")
        
        try:
            # Build and start containers
            subprocess.run(['docker-compose', 'up', '-d', '--build'], 
                         check=True, cwd=self.project_root)
            
            # Wait for services to be ready
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Waiting for services...", total=None)
                time.sleep(10)
            
            console.print("[green]✓ Docker system started successfully[/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error starting Docker system: {e}[/red]")
            return False
    
    def stop_docker_system(self):
        """Stop the Docker system"""
        console.print("[yellow]Stopping Docker system...[/yellow]")
        
        try:
            subprocess.run(['docker-compose', 'down'], 
                         check=True, cwd=self.project_root)
            console.print("[green]✓ Docker system stopped[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error stopping Docker system: {e}[/red]")
    
    def start_local_system(self):
        """Start the system locally (without Docker)"""
        console.print("[yellow]Starting local system...[/yellow]")
        
        # Start GA servers
        self.start_process("GA-A", [
            sys.executable, "-m", "ga.server",
            "--data-dir", "./data/siteA",
            "--node-id", "A",
            "--pretty"
        ])
        
        self.start_process("GA-B", [
            sys.executable, "-m", "ga.server",
            "--data-dir", "./data/siteB", 
            "--node-id", "B",
            "--pretty"
        ])
        
        # Start Actors
        self.start_process("AP", [
            sys.executable, "-m", "actors.prestamo",
            "--pretty"
        ])
        
        self.start_process("AR", [
            sys.executable, "-m", "actors.renovacion",
            "--pretty"
        ])
        
        self.start_process("AD", [
            sys.executable, "-m", "actors.devolucion",
            "--pretty"
        ])
        
        # Start GC
        self.start_process("GC", [
            sys.executable, "-m", "gestor_central.server",
            "--mode", "serial",
            "--pretty"
        ])
        
        # Wait for services
        time.sleep(5)
        console.print("[green]✓ Local system started[/green]")
    
    def start_process(self, name: str, cmd: List[str]):
        """Start a process and track it"""
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes[name] = process
            console.print(f"[green]✓ Started {name}[/green]")
        except Exception as e:
            console.print(f"[red]Error starting {name}: {e}[/red]")
    
    def stop_local_system(self):
        """Stop all local processes"""
        console.print("[yellow]Stopping local system...[/yellow]")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                console.print(f"[green]✓ Stopped {name}[/green]")
            except subprocess.TimeoutExpired:
                process.kill()
                console.print(f"[yellow]Force killed {name}[/yellow]")
            except Exception as e:
                console.print(f"[red]Error stopping {name}: {e}[/red]")
        
        self.processes.clear()
    
    def test_system(self):
        """Test the system with sample requests"""
        console.print("[yellow]Testing system...[/yellow]")
        
        # Test loan request
        test_request = {
            'id': 'test-1',
            'sedeId': 'A',
            'userId': 'u-test-1',
            'op': 'PRESTAR',
            'libroCodigo': 'ISBN-0001',
            'timestamp': int(time.time() * 1000)
        }
        
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            socket.send_json(test_request)
            response = socket.recv_json()
            
            console.print(f"[green]✓ Test successful: {response}[/green]")
            
            socket.close()
            context.term()
            return True
            
        except Exception as e:
            console.print(f"[red]Test failed: {e}[/red]")
            return False
    
    def run_load_test(self, duration: int = 60, ps_per_site: int = 2):
        """Run a load test"""
        console.print(f"[yellow]Running load test ({duration}s, {ps_per_site} PS per site)...[/yellow]")
        
        cmd = [
            sys.executable, "tools/spawn_ps.py",
            "--ps-per-site", str(ps_per_site),
            "--sites", "A,B",
            "--duration-sec", str(duration),
            "--gc", "tcp://127.0.0.1:5555",
            "--mode", "serial",
            "--out", "metrics/results.csv"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✓ Load test completed[/green]")
                return True
            else:
                console.print(f"[red]Load test failed: {result.stderr}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error running load test: {e}[/red]")
            return False
    
    def generate_charts(self):
        """Generate performance charts"""
        console.print("[yellow]Generating charts...[/yellow]")
        
        cmd = [
            sys.executable, "tools/charts.py",
            "--csv", "metrics/results.csv",
            "--outdir", "metrics/"
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            console.print("[green]✓ Charts generated[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error generating charts: {e}[/red]")
            return False
    
    def show_logs(self, service: str = "all"):
        """Show logs for services"""
        if service == "all":
            # Show Docker logs
            if self.check_docker():
                try:
                    subprocess.run(['docker-compose', 'logs', '-f'], 
                                 cwd=self.project_root)
                except KeyboardInterrupt:
                    pass
            else:
                # Show local process logs
                for name, process in self.processes.items():
                    console.print(f"[blue]=== {name} Logs ===[/blue]")
                    if process.stdout:
                        for line in iter(process.stdout.readline, ''):
                            console.print(line.strip())
        else:
            # Show specific service logs
            try:
                subprocess.run(['docker-compose', 'logs', '-f', service], 
                             cwd=self.project_root)
            except KeyboardInterrupt:
                pass
    
    def show_status(self):
        """Show system status"""
        table = Table(title="System Status", box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Port", style="yellow")
        
        # Check Docker services
        if self.check_docker():
            try:
                result = subprocess.run(['docker-compose', 'ps'], 
                                      capture_output=True, text=True, 
                                      cwd=self.project_root)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[2:]  # Skip header
                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                service = parts[0]
                                status = parts[1]
                                port = "Multiple" if "sitio" in service else "N/A"
                                table.add_row(service, status, port)
            except:
                pass
        
        # Check local processes
        for name, process in self.processes.items():
            status = "Running" if process.poll() is None else "Stopped"
            port = self.get_service_port(name)
            table.add_row(name, status, port)
        
        console.print(table)
    
    def get_service_port(self, service: str) -> str:
        """Get the port for a service"""
        ports = {
            "GC": "5555",
            "AP": "5557", 
            "GA-A": "5560",
            "GA-B": "5561",
            "AR": "N/A",
            "AD": "N/A"
        }
        return ports.get(service, "N/A")

# Global system manager
system_manager = SystemManager()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    console.print("\n[yellow]Shutting down system...[/yellow]")
    system_manager.stop_local_system()
    system_manager.stop_docker_system()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

@app.command()
def main():
    """Main menu interface for the distributed library system"""
    
    console.print(Panel.fit(
        "[bold blue]Distributed Library System[/bold blue]\n"
        "[dim]University Ada Lovelace - Systems Project[/dim]",
        border_style="blue"
    ))
    
    # Check dependencies
    if not system_manager.check_dependencies():
        console.print("[red]Please install dependencies first: pip install -r requirements.txt[/red]")
        return
    
    while True:
        console.print("\n" + "="*60)
        console.print("[bold cyan]Main Menu[/bold cyan]")
        console.print("="*60)
        
        # System status
        system_manager.show_status()
        
        console.print("\n[bold yellow]Available Options:[/bold yellow]")
        console.print("1. [green]Setup & Data[/green] - Generate sample data")
        console.print("2. [blue]Docker Mode[/blue] - Run with Docker (Recommended)")
        console.print("3. [blue]Local Mode[/blue] - Run locally without Docker")
        console.print("4. [yellow]Test System[/yellow] - Test with sample requests")
        console.print("5. [magenta]Load Test[/magenta] - Run performance tests")
        console.print("6. [cyan]Generate Charts[/cyan] - Create performance charts")
        console.print("7. [red]View Logs[/red] - Monitor system logs")
        console.print("8. [orange]Stop System[/orange] - Stop all services")
        console.print("9. [dim]Exit[/dim] - Exit the program")
        
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])
        
        if choice == "1":
            system_manager.generate_sample_data()
            
        elif choice == "2":
            if not system_manager.check_docker():
                console.print("[red]Docker is not available. Please install Docker first.[/red]")
                continue
            
            if Confirm.ask("Start Docker system?"):
                system_manager.start_docker_system()
                
        elif choice == "3":
            if Confirm.ask("Start local system?"):
                system_manager.start_local_system()
                
        elif choice == "4":
            if system_manager.test_system():
                console.print("[green]System is working correctly![/green]")
            else:
                console.print("[red]System test failed. Check if services are running.[/red]")
                
        elif choice == "5":
            duration = int(Prompt.ask("Test duration (seconds)", default="60"))
            ps_per_site = int(Prompt.ask("PS per site", default="2"))
            
            if system_manager.run_load_test(duration, ps_per_site):
                console.print("[green]Load test completed successfully![/green]")
                
        elif choice == "6":
            if system_manager.generate_charts():
                console.print("[green]Charts generated in metrics/ directory[/green]")
                
        elif choice == "7":
            service = Prompt.ask("Service to monitor", default="all")
            console.print("[yellow]Press Ctrl+C to stop monitoring[/yellow]")
            try:
                system_manager.show_logs(service)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped monitoring[/yellow]")
                
        elif choice == "8":
            if Confirm.ask("Stop all services?"):
                system_manager.stop_local_system()
                system_manager.stop_docker_system()
                
        elif choice == "9":
            if Confirm.ask("Exit the program?"):
                system_manager.stop_local_system()
                system_manager.stop_docker_system()
                console.print("[green]Goodbye![/green]")
                break

if __name__ == "__main__":
    app()
