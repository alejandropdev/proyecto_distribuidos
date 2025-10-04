"""
Actor Préstamo (AP) - Processes loan requests.
REP server that receives requests from GC and calls GA.checkAndLoan.
"""

import os
import sys
import signal
import zmq
import typer
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import APRequest, APReply
from common.logging_utils import log_message, setup_pretty_logging
from common.env import get_env_optional

# Load environment variables
load_dotenv()

app = typer.Typer()


class ActorPrestamo:
    """Actor that processes loan requests from GC via REQ/REP"""
    
    def __init__(self, pretty: bool = False):
        self.pretty = pretty
        self.running = True
        
        # Configuration from environment
        self.ap_rep_bind = get_env_optional("AP_REP_BIND", "tcp://0.0.0.0:5557")
        self.ga_rep_bind = get_env_optional("GA_REP_BIND", "tcp://127.0.0.1:5560")
        
        # ZMQ context and sockets
        self.context = zmq.Context()
        self.rep_socket = None
        self.req_socket = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message("AP", "shutdown", "PRESTAR", "recibido", f"Received signal {signum}", self.pretty)
        self.running = False
    
    def _setup_sockets(self):
        """Setup ZMQ sockets for communication"""
        # REP socket to receive requests from GC
        self.rep_socket = self.context.socket(zmq.REP)
        self.rep_socket.bind(self.ap_rep_bind)
        
        # REQ socket to communicate with GA
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(self.ga_rep_bind)
        
        log_message("AP", "setup", "PRESTAR", "recibido", 
                   f"Listening on {self.ap_rep_bind}, connected to GA at {self.ga_rep_bind}", self.pretty)
    
    def _process_prestamo_request(self, request_data: dict) -> dict:
        """Process a loan request from GC"""
        try:
            # Validate request with Pydantic
            ap_request = APRequest.model_validate(request_data)
            
            # Log received request
            log_message("AP", ap_request.id, "PRESTAR", "recibido", 
                       f"Processing loan request for user {ap_request.userId}, book {ap_request.libroCodigo}", self.pretty)
            
            # Prepare GA request
            ga_request = {
                "method": "checkAndLoan",
                "payload": {
                    "id": ap_request.id,
                    "libroCodigo": ap_request.libroCodigo,
                    "userId": ap_request.userId
                }
            }
            
            # Send request to GA
            self.req_socket.send_json(ga_request)
            
            # Wait for response
            ga_response = self.req_socket.recv_json()
            
            # Map GA response to AP response format
            if ga_response.get("ok", False):
                due_date = ga_response.get("metadata", {}).get("dueDate")
                log_message("AP", ap_request.id, "PRESTAR", "aplicado", 
                           f"Loan successful for user {ap_request.userId}, due date: {due_date}", self.pretty)
                
                return {
                    "ok": True,
                    "reason": None,
                    "metadata": {"dueDate": due_date}
                }
            else:
                reason = ga_response.get("reason", "Unknown error")
                log_message("AP", ap_request.id, "PRESTAR", "error", 
                           f"Loan failed for user {ap_request.userId}: {reason}", self.pretty)
                
                return {
                    "ok": False,
                    "reason": reason,
                    "metadata": None
                }
                
        except Exception as e:
            log_message("AP", "unknown", "PRESTAR", "error", 
                       f"Error processing loan request: {str(e)}", self.pretty)
            
            return {
                "ok": False,
                "reason": f"Internal error: {str(e)}",
                "metadata": None
            }
    
    def run(self):
        """Main run loop for the actor"""
        try:
            self._setup_sockets()
            
            log_message("AP", "startup", "PRESTAR", "recibido", 
                       "Actor Préstamo started, listening for requests", self.pretty)
            
            while self.running:
                try:
                    # Poll for requests with timeout
                    if self.rep_socket.poll(1000):  # 1 second timeout
                        # Receive request
                        request_data = self.rep_socket.recv_json()
                        
                        # Process request
                        response = self._process_prestamo_request(request_data)
                        
                        # Send response
                        self.rep_socket.send_json(response)
                    
                except zmq.Again:
                    # Timeout, continue
                    continue
                except Exception as e:
                    log_message("AP", "error", "PRESTAR", "error", 
                               f"Error in main loop: {str(e)}", self.pretty)
                    break
            
        except Exception as e:
            log_message("AP", "fatal", "PRESTAR", "error", 
                       f"Fatal error: {str(e)}", self.pretty)
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        if self.rep_socket:
            self.rep_socket.close()
        if self.req_socket:
            self.req_socket.close()
        if self.context:
            self.context.term()
        
        log_message("AP", "shutdown", "PRESTAR", "recibido", "Actor Préstamo stopped", self.pretty)


@app.command()
def main(
    pretty: bool = typer.Option(False, "--pretty", help="Use pretty logging format")
):
    """Start Actor Préstamo (AP)"""
    if pretty:
        setup_pretty_logging()
    
    actor = ActorPrestamo(pretty=pretty)
    actor.run()


if __name__ == "__main__":
    app()
