#!/usr/bin/env python3
"""
Log Monitor for Distributed Library System
=========================================

Real-time log monitoring with filtering and highlighting for the distributed library system.
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import argparse

try:
    import zmq
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    from rich.prompt import Prompt, Confirm
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

class LogMonitor:
    """Real-time log monitoring with filtering and analysis"""
    
    def __init__(self):
        self.console = Console()
        self.project_root = Path(__file__).parent.parent
        self.services = {
            'GC': {'port': 5555, 'color': 'blue'},
            'AP': {'port': 5557, 'color': 'green'},
            'AR': {'port': None, 'color': 'yellow'},
            'AD': {'port': None, 'color': 'magenta'},
            'GA-A': {'port': 5560, 'color': 'cyan'},
            'GA-B': {'port': 5561, 'color': 'red'}
        }
        self.log_buffer: List[Dict] = []
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'operations': {'PRESTAR': 0, 'RENOVAR': 0, 'DEVOLVER': 0}
        }
    
    def check_docker_status(self) -> bool:
        """Check if Docker containers are running"""
        try:
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True,
                                  cwd=self.project_root)
            return 'sitio-a' in result.stdout and 'sitio-b' in result.stdout
        except:
            return False
    
    def get_docker_logs(self, service: str = None) -> List[str]:
        """Get logs from Docker containers"""
        try:
            cmd = ['docker-compose', 'logs', '--tail=100']
            if service:
                cmd.append(service)
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=self.project_root)
            return result.stdout.split('\n') if result.returncode == 0 else []
        except:
            return []
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a log line and extract structured information"""
        try:
            # Try to parse as JSON first
            if line.strip().startswith('{'):
                return json.loads(line.strip())
            
            # Parse structured log format
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    return {
                        'timestamp': parts[0].strip(),
                        'service': parts[1].strip(),
                        'level': parts[2].strip(),
                        'message': parts[3].strip()
                    }
            
            return None
        except:
            return None
    
    def update_stats(self, log_entry: Dict):
        """Update statistics based on log entry"""
        if 'op' in log_entry:
            self.stats['total_requests'] += 1
            op = log_entry['op']
            if op in self.stats['operations']:
                self.stats['operations'][op] += 1
            
            if log_entry.get('status') == 'OK':
                self.stats['successful_requests'] += 1
            elif log_entry.get('status') == 'ERROR':
                self.stats['failed_requests'] += 1
    
    def create_status_table(self) -> Table:
        """Create a status table showing system metrics"""
        table = Table(title="System Status", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(self.stats['total_requests']))
        table.add_row("Successful", str(self.stats['successful_requests']))
        table.add_row("Failed", str(self.stats['failed_requests']))
        table.add_row("", "")  # Empty row
        
        table.add_row("PRESTAR", str(self.stats['operations']['PRESTAR']))
        table.add_row("RENOVAR", str(self.stats['operations']['RENOVAR']))
        table.add_row("DEVOLVER", str(self.stats['operations']['DEVOLVER']))
        
        return table
    
    def create_log_table(self, logs: List[Dict]) -> Table:
        """Create a table showing recent logs"""
        table = Table(title="Recent Logs", box=box.ROUNDED)
        table.add_column("Time", style="dim")
        table.add_column("Service", style="cyan")
        table.add_column("Operation", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        # Show last 10 logs
        recent_logs = logs[-10:] if logs else []
        
        for log in recent_logs:
            timestamp = log.get('timestamp', 'N/A')
            service = log.get('service', log.get('proc', 'N/A'))
            operation = log.get('op', 'N/A')
            status = log.get('status', log.get('stage', 'N/A'))
            details = log.get('detail', log.get('message', 'N/A'))
            
            # Color code status
            status_color = 'green' if status in ['OK', 'RECIBIDO'] else 'red' if status == 'ERROR' else 'yellow'
            
            table.add_row(
                timestamp,
                service,
                operation,
                Text(status, style=status_color),
                details[:50] + '...' if len(details) > 50 else details
            )
        
        return table
    
    def create_layout(self) -> Layout:
        """Create the main layout for the monitor"""
        layout = Layout()
        
        layout.split_column(
            Layout(Panel(self.create_status_table(), title="Statistics"), size=12),
            Layout(Panel(self.create_log_table(self.log_buffer), title="Live Logs"), size=20)
        )
        
        return layout
    
    def monitor_docker_logs(self, service: str = None):
        """Monitor Docker container logs in real-time"""
        self.console.print("[yellow]Starting Docker log monitoring...[/yellow]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        try:
            with Live(self.create_layout(), refresh_per_second=2) as live:
                while True:
                    logs = self.get_docker_logs(service)
                    parsed_logs = []
                    
                    for line in logs:
                        if line.strip():
                            parsed = self.parse_log_line(line)
                            if parsed:
                                parsed_logs.append(parsed)
                                self.update_stats(parsed)
                    
                    self.log_buffer.extend(parsed_logs[-20:])  # Keep last 20 logs
                    if len(self.log_buffer) > 100:
                        self.log_buffer = self.log_buffer[-100:]
                    
                    live.update(self.create_layout())
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitoring stopped[/yellow]")
    
    def monitor_zmq_messages(self):
        """Monitor ZeroMQ messages in real-time"""
        self.console.print("[yellow]Starting ZeroMQ message monitoring...[/yellow]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        context = zmq.Context()
        
        # Subscribe to GC PUB socket
        subscriber = context.socket(zmq.SUB)
        subscriber.connect('tcp://localhost:5556')
        subscriber.setsockopt(zmq.SUBSCRIBE, b'')  # Subscribe to all topics
        
        try:
            with Live(self.create_layout(), refresh_per_second=2) as live:
                while True:
                    try:
                        # Check for messages with timeout
                        if subscriber.poll(100):  # 100ms timeout
                            topic = subscriber.recv_string()
                            message = subscriber.recv_json()
                            
                            log_entry = {
                                'timestamp': datetime.now().strftime('%H:%M:%S'),
                                'service': 'GC-PUB',
                                'topic': topic,
                                'message': str(message)
                            }
                            
                            self.log_buffer.append(log_entry)
                            if len(self.log_buffer) > 100:
                                self.log_buffer = self.log_buffer[-100:]
                            
                            live.update(self.create_layout())
                    
                    except zmq.Again:
                        # No message received, continue
                        pass
                    
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitoring stopped[/yellow]")
        finally:
            subscriber.close()
            context.term()
    
    def show_service_status(self):
        """Show status of all services"""
        table = Table(title="Service Status", box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Port", style="yellow")
        table.add_column("Health", style="magenta")
        
        # Check Docker services
        if self.check_docker_status():
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
                                service = parts[0]
                                status = parts[1]
                                port = "Multiple" if "sitio" in service else "N/A"
                                health = "✓" if status == "Up" else "✗"
                                table.add_row(service, status, port, health)
            except:
                pass
        
        # Check individual services
        for service, config in self.services.items():
            if config['port']:
                # Try to connect to service
                try:
                    context = zmq.Context()
                    socket = context.socket(zmq.REQ)
                    socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
                    socket.connect(f'tcp://localhost:{config["port"]}')
                    
                    # Send health check
                    socket.send_json({'status': 'check'})
                    socket.recv_json()
                    
                    table.add_row(service, "Running", str(config['port']), "✓")
                    socket.close()
                    context.term()
                    
                except:
                    table.add_row(service, "Stopped", str(config['port']), "✗")
            else:
                table.add_row(service, "N/A", "N/A", "N/A")
        
        self.console.print(table)
    
    def run_interactive_monitor(self):
        """Run interactive monitoring interface"""
        while True:
            self.console.print("\n" + "="*60)
            self.console.print("[bold cyan]Log Monitor Menu[/bold cyan]")
            self.console.print("="*60)
            
            self.console.print("\n[bold yellow]Available Options:[/bold yellow]")
            self.console.print("1. [blue]Monitor Docker Logs[/blue] - Real-time Docker container logs")
            self.console.print("2. [green]Monitor ZeroMQ Messages[/green] - Real-time message monitoring")
            self.console.print("3. [cyan]Show Service Status[/cyan] - Check all services")
            self.console.print("4. [yellow]View Recent Logs[/yellow] - Show recent log entries")
            self.console.print("5. [red]Exit[/red] - Exit the monitor")
            
            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                service = Prompt.ask("Service to monitor (or 'all')", default="all")
                service = None if service == "all" else service
                self.monitor_docker_logs(service)
                
            elif choice == "2":
                self.monitor_zmq_messages()
                
            elif choice == "3":
                self.show_service_status()
                
            elif choice == "4":
                self.console.print(self.create_log_table(self.log_buffer))
                
            elif choice == "5":
                if Confirm.ask("Exit the monitor?"):
                    break

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Log Monitor for Distributed Library System")
    parser.add_argument('--service', help='Specific service to monitor')
    parser.add_argument('--zmq', action='store_true', help='Monitor ZeroMQ messages')
    parser.add_argument('--status', action='store_true', help='Show service status')
    parser.add_argument('--interactive', action='store_true', help='Run interactive mode')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    
    if args.status:
        monitor.show_service_status()
    elif args.zmq:
        monitor.monitor_zmq_messages()
    elif args.service:
        monitor.monitor_docker_logs(args.service)
    elif args.interactive:
        monitor.run_interactive_monitor()
    else:
        # Default: interactive mode
        monitor.run_interactive_monitor()

if __name__ == "__main__":
    main()
