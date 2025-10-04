"""
PS (Proceso Solicitante) client implementation.
Sends requests to GC and measures latency for PRESTAR operations.
"""

import json
import time
import zmq
import typer
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from common.models import ClientRequest, GCReply
from common.logging_utils import log_message, setup_pretty_logging
from common.time_utils import now_ms
from common.env import GC_BIND


app = typer.Typer(help="PS (Proceso Solicitante) Client")


class PSClient:
    """PS client for sending requests to GC"""
    
    def __init__(self, gc_endpoint: str, pretty: bool = False):
        self.gc_endpoint = gc_endpoint
        self.pretty = pretty
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(gc_endpoint)
        
        # Set socket timeout
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        
        log_message(
            "PS", "startup", "INIT", "recibido",
            f"PS client connected to {gc_endpoint}",
            pretty
        )
    
    def send_request(self, request: ClientRequest) -> Tuple[GCReply, Optional[float]]:
        """
        Send request to GC and measure latency.
        
        Args:
            request: Client request to send
            
        Returns:
            Tuple of (response, latency_ms) where latency is None for non-PRESTAR operations
        """
        start_time = None
        if request.op == "PRESTAR":
            start_time = now_ms()
        
        try:
            # Send request
            self.socket.send_string(json.dumps(request.model_dump()))
            
            log_message(
                "PS", request.id, request.op, "enviado",
                f"Sent request to GC",
                self.pretty
            )
            
            # Receive response
            response_data = self.socket.recv_string()
            response = GCReply(**json.loads(response_data))
            
            # Calculate latency for PRESTAR operations
            latency_ms = None
            if request.op == "PRESTAR" and start_time:
                latency_ms = now_ms() - start_time
            
            log_message(
                "PS", request.id, request.op, "aplicado",
                f"Received response: {response.status}",
                self.pretty
            )
            
            return response, latency_ms
            
        except zmq.Again:
            log_message(
                "PS", request.id, request.op, "error",
                "Timeout waiting for GC response",
                self.pretty
            )
            # Return error response
            error_response = GCReply(
                id=request.id,
                status="ERROR",
                reason="Timeout waiting for GC response"
            )
            return error_response, None
            
        except Exception as e:
            log_message(
                "PS", request.id, request.op, "error",
                f"Request failed: {str(e)}",
                self.pretty
            )
            # Return error response
            error_response = GCReply(
                id=request.id,
                status="ERROR",
                reason=str(e)
            )
            return error_response, None
    
    def close(self):
        """Close the PS client"""
        self.socket.close()
        self.context.term()


def load_requests_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load requests from peticiones.txt file.
    
    Expected format:
    PRESTAR ISBN-0001 u-1
    RENOVAR ISBN-0100 u-17
    DEVOLVER ISBN-0099 u-5
    
    Returns:
        List of request dictionaries
    """
    requests = []
    
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) != 3:
                    print(f"Warning: Invalid line {line_num}: {line}")
                    continue
                
                op, libro_codigo, user_id = parts
                
                if op not in ["PRESTAR", "RENOVAR", "DEVOLVER"]:
                    print(f"Warning: Unknown operation '{op}' in line {line_num}")
                    continue
                
                requests.append({
                    "op": op,
                    "libroCodigo": libro_codigo,
                    "userId": user_id
                })
    
    except FileNotFoundError:
        typer.echo(f"Error: File {file_path} not found", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error reading file {file_path}: {e}", err=True)
        raise typer.Exit(1)
    
    return requests


@app.command()
def main(
    sede: str = typer.Option(
        "A", "--sede", "-s",
        help="Site ID (A or B)"
    ),
    file: Path = typer.Option(
        "data/ejemplos/peticiones_sample.txt", "--file", "-f",
        help="Path to peticiones.txt file"
    ),
    gc: str = typer.Option(
        GC_BIND, "--gc", "-g",
        help="GC endpoint (default: from env)"
    ),
    pretty: bool = typer.Option(
        False, "--pretty", "-p",
        help="Enable pretty logging"
    ),
    delay_ms: int = typer.Option(
        50, "--delay", "-d",
        help="Delay between requests in milliseconds"
    )
):
    """
    Run PS client with requests from file.
    
    Reads requests from peticiones.txt and sends them to GC,
    measuring latency for PRESTAR operations.
    """
    
    # Validate sede
    if sede not in ["A", "B"]:
        typer.echo("Error: sede must be 'A' or 'B'", err=True)
        raise typer.Exit(1)
    
    # Setup logging
    if pretty:
        setup_pretty_logging()
    
    # Load requests
    typer.echo(f"Loading requests from {file}...")
    request_data = load_requests_from_file(file)
    
    if not request_data:
        typer.echo("No valid requests found in file", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Loaded {len(request_data)} requests")
    
    # Create PS client
    client = PSClient(gc, pretty)
    
    try:
        # Process requests
        prestar_latencies = []
        prestar_count = 0
        
        for i, req_data in enumerate(request_data, 1):
            # Create request
            request = ClientRequest(
                sedeId=sede,
                userId=req_data["userId"],
                op=req_data["op"],
                libroCodigo=req_data["libroCodigo"],
                timestamp=now_ms()
            )
            
            typer.echo(f"Request {i}/{len(request_data)}: {request.op} {request.libroCodigo}")
            
            # Send request
            response, latency = client.send_request(request)
            
            # Collect metrics for PRESTAR operations
            if request.op == "PRESTAR":
                prestar_count += 1
                if latency is not None:
                    prestar_latencies.append(latency)
                    typer.echo(f"  Latency: {latency:.2f}ms")
                
                if response.status == "OK":
                    typer.echo(f"  Success: Due date {response.dueDate}")
                else:
                    typer.echo(f"  Error: {response.reason}")
            else:
                typer.echo(f"  Response: {response.status}")
            
            # Add delay between requests
            if i < len(request_data):
                time.sleep(delay_ms / 1000.0)
        
        # Print summary
        typer.echo("\n" + "="*50)
        typer.echo("SUMMARY")
        typer.echo("="*50)
        typer.echo(f"Total requests: {len(request_data)}")
        typer.echo(f"PRESTAR requests: {prestar_count}")
        
        if prestar_latencies:
            avg_latency = sum(prestar_latencies) / len(prestar_latencies)
            typer.echo(f"Average PRESTAR latency: {avg_latency:.2f}ms")
            typer.echo(f"Min latency: {min(prestar_latencies):.2f}ms")
            typer.echo(f"Max latency: {max(prestar_latencies):.2f}ms")
    
    finally:
        client.close()


if __name__ == "__main__":
    app()
