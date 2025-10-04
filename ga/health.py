"""
GA Health module - Handles heartbeat publishing and health check endpoint.
Provides health monitoring for GA nodes.
"""

import os
import sys
import signal
import zmq
import threading
import time
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message
from common.env import get_env_optional
from common.time_utils import now_ms

# Load environment variables
load_dotenv()


class GAHealth:
    """Health monitoring for GA nodes"""
    
    def __init__(self, node_id: str = "A"):
        self.node_id = node_id
        self.running = False
        
        # Configuration from environment
        self.heartbeat_pub_bind = get_env_optional("GA_HEARTBEAT_PUB_BIND", "tcp://0.0.0.0:5565")
        self.health_rep_bind = get_env_optional("GA_HEALTH_REP_BIND", "tcp://0.0.0.0:5564")
        self.heartbeat_interval_ms = int(get_env_optional("GA_HEARTBEAT_INTERVAL_MS", "2000"))
        
        # ZMQ context and sockets
        self.context = zmq.Context()
        self.heartbeat_pub_socket = None
        self.health_rep_socket = None
        
        # Threading
        self.heartbeat_thread = None
        self.health_thread = None
        
        # Statistics
        self.heartbeats_sent = 0
        self.health_checks_responded = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message("GA", "health", "SHUTDOWN", "recibido", f"Received signal {signum}")
        self.stop()
    
    def _setup_sockets(self):
        """Setup ZMQ sockets for health monitoring"""
        # PUB socket for heartbeat
        self.heartbeat_pub_socket = self.context.socket(zmq.PUB)
        self.heartbeat_pub_socket.bind(self.heartbeat_pub_bind)
        
        # REP socket for health checks
        self.health_rep_socket = self.context.socket(zmq.REP)
        self.health_rep_socket.bind(self.health_rep_bind)
        
        log_message("GA", "health", "SETUP", "recibido", 
                   f"Health sockets setup - Heartbeat PUB: {self.heartbeat_pub_bind}, Health REP: {self.health_rep_bind}")
    
    def _publish_heartbeat(self):
        """Publish heartbeat message"""
        try:
            heartbeat = {
                "node": self.node_id,
                "ts": now_ms(),
                "status": "alive",
                "heartbeat_count": self.heartbeats_sent
            }
            
            self.heartbeat_pub_socket.send_json(heartbeat)
            self.heartbeats_sent += 1
            
            log_message("GA", "heartbeat", "HEARTBEAT", "enviado", 
                       f"Heartbeat {self.heartbeats_sent} published for node {self.node_id}")
            
        except Exception as e:
            log_message("GA", "heartbeat", "HEARTBEAT", "error", 
                       f"Error publishing heartbeat: {str(e)}")
    
    def _heartbeat_loop(self):
        """Main loop for publishing heartbeats"""
        log_message("GA", "health", "HEARTBEAT", "recibido", 
                   "Starting heartbeat loop")
        
        while self.running:
            try:
                self._publish_heartbeat()
                time.sleep(self.heartbeat_interval_ms / 1000.0)
                
            except Exception as e:
                log_message("GA", "health", "HEARTBEAT", "error", 
                           f"Error in heartbeat loop: {str(e)}")
                break
        
        log_message("GA", "health", "HEARTBEAT", "recibido", "Heartbeat loop stopped")
    
    def _health_check_loop(self):
        """Main loop for responding to health check requests"""
        log_message("GA", "health", "HEALTH_CHECK", "recibido", 
                   "Starting health check loop")
        
        while self.running:
            try:
                if self.health_rep_socket.poll(1000):  # 1 second timeout
                    # Receive health check request
                    request = self.health_rep_socket.recv_json()
                    
                    # Respond with health status
                    health_response = {
                        "status": "ok",
                        "node": self.node_id,
                        "ts": now_ms(),
                        "heartbeats_sent": self.heartbeats_sent,
                        "health_checks_responded": self.health_checks_responded
                    }
                    
                    self.health_rep_socket.send_json(health_response)
                    self.health_checks_responded += 1
                    
                    log_message("GA", "health", "HEALTH_CHECK", "aplicado", 
                               f"Health check request responded for node {self.node_id}")
                else:
                    # Timeout, continue
                    continue
                    
            except zmq.Again:
                # Timeout, continue
                continue
            except Exception as e:
                log_message("GA", "health", "HEALTH_CHECK", "error", 
                           f"Error in health check loop: {str(e)}")
                break
        
        log_message("GA", "health", "HEALTH_CHECK", "recibido", "Health check loop stopped")
    
    def start(self):
        """Start health monitoring service"""
        if self.running:
            return
        
        try:
            self._setup_sockets()
            self.running = True
            
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            # Start health check thread
            self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_thread.start()
            
            log_message("GA", "health", "START", "recibido", 
                       f"Health monitoring started for node {self.node_id}")
            
        except Exception as e:
            log_message("GA", "health", "START", "error", 
                       f"Error starting health monitoring: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop health monitoring service"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for threads to finish
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
        
        if self.health_thread and self.health_thread.is_alive():
            self.health_thread.join(timeout=2)
        
        # Close sockets
        if self.heartbeat_pub_socket:
            self.heartbeat_pub_socket.close()
        if self.health_rep_socket:
            self.health_rep_socket.close()
        if self.context:
            self.context.term()
        
        log_message("GA", "health", "STOP", "recibido", 
                   f"Health monitoring stopped for node {self.node_id}")
    
    def get_health_stats(self) -> dict:
        """Get health monitoring statistics"""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "heartbeats_sent": self.heartbeats_sent,
            "health_checks_responded": self.health_checks_responded,
            "heartbeat_interval_ms": self.heartbeat_interval_ms
        }
