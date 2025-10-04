"""
Actor Renovación (AR) - Processes renovation requests.
Subscribes to GC PUB/SUB for RENOVACION topic and calls GA.renovar.
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

from common.models import ActorMessage
from common.logging_utils import log_message, setup_pretty_logging
from common.env import get_env_optional

# Load environment variables
load_dotenv()

app = typer.Typer()


class ActorRenovacion:
    """Actor that processes renovation requests from GC via PUB/SUB"""
    
    def __init__(self, pretty: bool = False):
        self.pretty = pretty
        self.running = True
        
        # Configuration from environment
        self.gc_pub_connect = get_env_optional("GC_PUB_CONNECT", "tcp://127.0.0.1:5556")
        self.topic_renovacion = get_env_optional("TOPIC_RENOVACION", "RENOVACION")
        self.ga_rep_bind = get_env_optional("GA_REP_BIND", "tcp://127.0.0.1:5560")
        
        # ZMQ context and sockets
        self.context = zmq.Context()
        self.sub_socket = None
        self.req_socket = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message("AR", "shutdown", "RENOVAR", "recibido", f"Received signal {signum}", self.pretty)
        self.running = False
    
    def _setup_sockets(self):
        """Setup ZMQ sockets for communication"""
        # SUB socket to receive messages from GC
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.gc_pub_connect)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, self.topic_renovacion.encode())
        
        # REQ socket to communicate with GA
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(self.ga_rep_bind)
        
        log_message("AR", "setup", "RENOVAR", "recibido", 
                   f"Connected to GC at {self.gc_pub_connect}, GA at {self.ga_rep_bind}", self.pretty)
    
    def _process_renovacion_message(self, message_data: bytes) -> bool:
        """Process a renovation message from GC"""
        try:
            # Parse the message (skip topic prefix)
            topic, message_json = message_data.split(b' ', 1)
            message_str = message_json.decode('utf-8')
            
            # Validate with Pydantic
            actor_msg = ActorMessage.model_validate_json(message_str)
            
            # Log received message
            log_message("AR", actor_msg.id, "RENOVAR", "recibido", 
                       f"Processing renovation for user {actor_msg.userId}, book {actor_msg.libroCodigo}", self.pretty)
            
            # Check if this is a RENOVAR operation
            if actor_msg.op != "RENOVAR":
                log_message("AR", actor_msg.id, "RENOVAR", "error", 
                           f"Received non-RENOVAR operation: {actor_msg.op}", self.pretty)
                return False
            
            # Prepare GA request
            ga_request = {
                "method": "renovar",
                "payload": {
                    "id": actor_msg.id,
                    "libroCodigo": actor_msg.libroCodigo,
                    "userId": actor_msg.userId,
                    "dueDateNew": actor_msg.dueDateNew
                }
            }
            
            # Send request to GA
            self.req_socket.send_json(ga_request)
            
            # Wait for response
            response = self.req_socket.recv_json()
            
            if response.get("ok", False):
                log_message("AR", actor_msg.id, "RENOVAR", "aplicado", 
                           f"Renovation successful for user {actor_msg.userId}, new due date: {actor_msg.dueDateNew}", self.pretty)
                return True
            else:
                log_message("AR", actor_msg.id, "RENOVAR", "error", 
                           f"Renovation failed: {response.get('reason', 'Unknown error')}", self.pretty)
                return False
                
        except Exception as e:
            log_message("AR", "unknown", "RENOVAR", "error", 
                       f"Error processing renovation message: {str(e)}", self.pretty)
            return False
    
    def run(self):
        """Main run loop for the actor"""
        try:
            self._setup_sockets()
            
            log_message("AR", "startup", "RENOVAR", "recibido", 
                       "Actor Renovación started, listening for messages", self.pretty)
            
            while self.running:
                try:
                    # Poll for messages with timeout
                    if self.sub_socket.poll(1000):  # 1 second timeout
                        message_data = self.sub_socket.recv()
                        self._process_renovacion_message(message_data)
                    
                except zmq.Again:
                    # Timeout, continue
                    continue
                except Exception as e:
                    log_message("AR", "error", "RENOVAR", "error", 
                               f"Error in main loop: {str(e)}", self.pretty)
                    break
            
        except Exception as e:
            log_message("AR", "fatal", "RENOVAR", "error", 
                       f"Fatal error: {str(e)}", self.pretty)
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        if self.sub_socket:
            self.sub_socket.close()
        if self.req_socket:
            self.req_socket.close()
        if self.context:
            self.context.term()
        
        log_message("AR", "shutdown", "RENOVAR", "recibido", "Actor Renovación stopped", self.pretty)


@app.command()
def main(
    pretty: bool = typer.Option(False, "--pretty", help="Use pretty logging format")
):
    """Start Actor Renovación (AR)"""
    if pretty:
        setup_pretty_logging()
    
    actor = ActorRenovacion(pretty=pretty)
    actor.run()


if __name__ == "__main__":
    app()
