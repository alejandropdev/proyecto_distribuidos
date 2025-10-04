"""
GA Server module - Main server that handles requests from actors.
Provides REP server with methods: renovar, devolver, checkAndLoan.
"""

import os
import sys
import signal
import zmq
import typer
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message, setup_pretty_logging
from common.env import get_env_optional
from .storage import GAStorage
from .oplog import GAOplog
from .replication import GAReplication
from .health import GAHealth

# Load environment variables
load_dotenv()

app = typer.Typer()


class GAServer:
    """Main GA server that handles requests from actors"""
    
    def __init__(self, data_dir: str, node_id: str = "A", pretty: bool = False):
        self.data_dir = data_dir
        self.node_id = node_id
        self.pretty = pretty
        self.running = True
        
        # Configuration from environment
        self.ga_rep_bind = get_env_optional("GA_REP_BIND", "tcp://0.0.0.0:5560")
        
        # Initialize components
        self.storage = GAStorage(data_dir)
        self.oplog = GAOplog(data_dir)
        self.replication = GAReplication(self.storage, self.oplog, node_id)
        self.health = GAHealth(node_id)
        
        # ZMQ context and socket
        self.context = zmq.Context()
        self.rep_socket = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message("GA", "server", "SHUTDOWN", "recibido", f"Received signal {signum}", self.pretty)
        self.running = False
    
    def _setup_socket(self):
        """Setup ZMQ REP socket for handling requests"""
        self.rep_socket = self.context.socket(zmq.REP)
        self.rep_socket.bind(self.ga_rep_bind)
        
        log_message("GA", "server", "SETUP", "recibido", 
                   f"GA server listening on {self.ga_rep_bind} for node {self.node_id}", self.pretty)
    
    def _process_request(self, request: Dict) -> Dict[str, Any]:
        """Process incoming request and return response"""
        try:
            method = request.get("method")
            payload = request.get("payload", {})
            
            if not method:
                return {
                    "ok": False,
                    "reason": "Missing method in request",
                    "metadata": None
                }
            
            # Route to appropriate method
            if method == "renovar":
                return self._handle_renovar(payload)
            elif method == "devolver":
                return self._handle_devolver(payload)
            elif method == "checkAndLoan":
                return self._handle_checkAndLoan(payload)
            else:
                return {
                    "ok": False,
                    "reason": f"Unknown method: {method}",
                    "metadata": None
                }
                
        except Exception as e:
            log_message("GA", "server", "REQUEST", "error", 
                       f"Error processing request: {str(e)}", self.pretty)
            return {
                "ok": False,
                "reason": f"Internal error: {str(e)}",
                "metadata": None
            }
    
    def _handle_renovar(self, payload: Dict) -> Dict[str, Any]:
        """Handle renovar request"""
        try:
            id = payload.get("id")
            codigo = payload.get("libroCodigo")
            userId = payload.get("userId")
            dueDateNew = payload.get("dueDateNew")
            
            if not all([id, codigo, userId, dueDateNew]):
                return {
                    "ok": False,
                    "reason": "Missing required fields for renovar",
                    "metadata": None
                }
            
            # Execute operation
            result = self.storage.renovar(id, codigo, userId, dueDateNew)
            
            # Log operation to oplog
            if result.get("ok", False):
                operation = {
                    "id": id,
                    "op": "RENOVAR",
                    "codigo": codigo,
                    "userId": userId,
                    "dueDateNew": dueDateNew
                }
                self.oplog.append_operation(operation)
                
                # Replicate to peer
                self.replication.replicate_operation(operation)
            
            return result
            
        except Exception as e:
            log_message("GA", payload.get("id", "unknown"), "RENOVAR", "error", 
                       f"Error in renovar handler: {str(e)}", self.pretty)
            return {
                "ok": False,
                "reason": f"Internal error: {str(e)}",
                "metadata": None
            }
    
    def _handle_devolver(self, payload: Dict) -> Dict[str, Any]:
        """Handle devolver request"""
        try:
            id = payload.get("id")
            codigo = payload.get("libroCodigo")
            userId = payload.get("userId")
            
            if not all([id, codigo, userId]):
                return {
                    "ok": False,
                    "reason": "Missing required fields for devolver",
                    "metadata": None
                }
            
            # Execute operation
            result = self.storage.devolver(id, codigo, userId)
            
            # Log operation to oplog
            if result.get("ok", False):
                operation = {
                    "id": id,
                    "op": "DEVOLVER",
                    "codigo": codigo,
                    "userId": userId
                }
                self.oplog.append_operation(operation)
                
                # Replicate to peer
                self.replication.replicate_operation(operation)
            
            return result
            
        except Exception as e:
            log_message("GA", payload.get("id", "unknown"), "DEVOLVER", "error", 
                       f"Error in devolver handler: {str(e)}", self.pretty)
            return {
                "ok": False,
                "reason": f"Internal error: {str(e)}",
                "metadata": None
            }
    
    def _handle_checkAndLoan(self, payload: Dict) -> Dict[str, Any]:
        """Handle checkAndLoan request"""
        try:
            id = payload.get("id")
            codigo = payload.get("libroCodigo")
            userId = payload.get("userId")
            
            if not all([id, codigo, userId]):
                return {
                    "ok": False,
                    "reason": "Missing required fields for checkAndLoan",
                    "metadata": None
                }
            
            # Execute operation
            result = self.storage.checkAndLoan(id, codigo, userId)
            
            # Log operation to oplog
            if result.get("ok", False):
                operation = {
                    "id": id,
                    "op": "PRESTAR",
                    "codigo": codigo,
                    "userId": userId
                }
                self.oplog.append_operation(operation)
                
                # Replicate to peer
                self.replication.replicate_operation(operation)
            
            return result
            
        except Exception as e:
            log_message("GA", payload.get("id", "unknown"), "PRESTAR", "error", 
                       f"Error in checkAndLoan handler: {str(e)}", self.pretty)
            return {
                "ok": False,
                "reason": f"Internal error: {str(e)}",
                "metadata": None
            }
    
    def run(self):
        """Main run loop for the GA server"""
        try:
            self._setup_socket()
            
            # Start replication and health services
            self.replication.start()
            self.health.start()
            
            log_message("GA", "server", "START", "recibido", 
                       f"GA server started for node {self.node_id}", self.pretty)
            
            while self.running:
                try:
                    # Poll for requests with timeout
                    if self.rep_socket.poll(1000):  # 1 second timeout
                        # Receive request
                        request = self.rep_socket.recv_json()
                        
                        # Process request
                        response = self._process_request(request)
                        
                        # Send response
                        self.rep_socket.send_json(response)
                    
                except zmq.Again:
                    # Timeout, continue
                    continue
                except Exception as e:
                    log_message("GA", "server", "REQUEST", "error", 
                               f"Error in main loop: {str(e)}", self.pretty)
                    break
            
        except Exception as e:
            log_message("GA", "server", "FATAL", "error", 
                       f"Fatal error: {str(e)}", self.pretty)
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        # Stop services
        self.replication.stop()
        self.health.stop()
        
        # Close socket
        if self.rep_socket:
            self.rep_socket.close()
        if self.context:
            self.context.term()
        
        log_message("GA", "server", "SHUTDOWN", "recibido", 
                   f"GA server stopped for node {self.node_id}", self.pretty)


@app.command()
def main(
    data_dir: str = typer.Option("./data/siteA", "--data-dir", help="Data directory for GA"),
    node_id: str = typer.Option("A", "--node-id", help="GA node identifier (A or B)"),
    pretty: bool = typer.Option(False, "--pretty", help="Use pretty logging format")
):
    """Start GA (Gestor de Almacenamiento) server"""
    if pretty:
        setup_pretty_logging()
    
    server = GAServer(data_dir=data_dir, node_id=node_id, pretty=pretty)
    server.run()


if __name__ == "__main__":
    app()
