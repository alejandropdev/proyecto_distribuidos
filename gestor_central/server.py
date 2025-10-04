"""
GC (Gestor Central) server implementation.
Handles PS requests via REQ/REP and publishes to actors via PUB/SUB.
"""

import signal
import sys
import typer
from typing import Optional
from common.env import GC_MODE
from common.logging_utils import setup_pretty_logging, log_message
from .modes import create_gc_mode


app = typer.Typer(help="GC (Gestor Central) Server")


@app.command()
def main(
    mode: Optional[str] = typer.Option(
        None, "--mode", "-m", 
        help="GC mode: serial or threaded (overrides GC_MODE env var)"
    ),
    workers: int = typer.Option(
        8, "--workers", "-w",
        help="Number of worker threads for threaded mode"
    ),
    pretty: bool = typer.Option(
        False, "--pretty", "-p",
        help="Enable pretty logging with rich"
    ),
    mock_ap: bool = typer.Option(
        False, "--mock-ap",
        help="Use mock AP responses for testing (bypasses real AP connection)"
    )
):
    """
    Start the GC server.
    
    The GC handles PS requests and routes them to appropriate actors:
    - RENOVAR/DEVOLVER: Published to topics for AR/AD
    - PRESTAR: Forwarded to AP via REQ/REP
    """
    
    # Setup logging
    if pretty:
        setup_pretty_logging()
    
    # Determine mode
    gc_mode = mode or GC_MODE
    
    if gc_mode not in ["serial", "threaded"]:
        typer.echo(f"Error: Invalid mode '{gc_mode}'. Must be 'serial' or 'threaded'", err=True)
        raise typer.Exit(1)
    
    # Create GC mode instance
    try:
        gc_server = create_gc_mode(gc_mode, workers, pretty, mock_ap)
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            log_message(
                "GC", "shutdown", "INIT", "recibido",
                f"Received signal {signum}, shutting down...",
                pretty
            )
            gc_server.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start server
        typer.echo(f"Starting GC server in {gc_mode} mode...")
        if gc_mode == "threaded":
            typer.echo(f"Using {workers} worker threads")
        
        gc_server.start()
        
    except KeyboardInterrupt:
        typer.echo("\nShutting down GC server...")
        gc_server.stop()
    except Exception as e:
        typer.echo(f"Error starting GC server: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
