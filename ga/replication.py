"""
GA Replication module - Handles PUB/SUB replication between GA_A and GA_B.
Provides asynchronous replication with idempotency guarantees.
"""

import os
import sys
import signal
import zmq
import threading
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message
from common.env import get_env_optional
from .storage import GAStorage
from .oplog import GAOplog

# Load environment variables
load_dotenv()


class GAReplication:
    """Handles replication between GA nodes using PUB/SUB"""
    
    def __init__(self, storage: GAStorage, oplog: GAOplog, node_id: str = "A"):
        self.storage = storage
        self.oplog = oplog
        self.node_id = node_id
        self.running = False
        
        # Configuration from environment
        self.repl_pub_bind = get_env_optional("GA_REPL_PUB_BIND", "tcp://0.0.0.0:5562")
        self.repl_sub_connect = get_env_optional("GA_REPL_SUB_CONNECT", "tcp://127.0.0.1:5563")
        self.snapshot_interval_ops = int(get_env_optional("SNAPSHOT_INTERVAL_OPS", "500"))
        
        # ZMQ context and sockets
        self.context = zmq.Context()
        self.pub_socket = None
        self.sub_socket = None
        
        # Threading
        self.replication_thread = None
        self.subscription_thread = None
        
        # Statistics
        self.operations_sent = 0
        self.operations_received = 0
        self.last_snapshot_ops = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message("GA", "replication", "SHUTDOWN", "recibido", f"Received signal {signum}")
        self.stop()
    
    def _setup_sockets(self):
        """Setup ZMQ sockets for replication"""
        # PUB socket to send operations to peer
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(self.repl_pub_bind)
        
        # SUB socket to receive operations from peer
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.repl_sub_connect)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
        
        log_message("GA", "replication", "SETUP", "recibido", 
                   f"Replication sockets setup - PUB: {self.repl_pub_bind}, SUB: {self.repl_sub_connect}")
    
    def _publish_operation(self, operation: Dict):
        """Publish operation to peer GA"""
        try:
            if self.pub_socket:
                # Add replication metadata
                replication_op = {
                    **operation,
                    "source_node": self.node_id,
                    "replication_ts": time.time() * 1000
                }
                
                self.pub_socket.send_json(replication_op)
                self.operations_sent += 1
                
                log_message("GA", operation.get("id", "unknown"), operation.get("op", "UNKNOWN"), "enviado", 
                           f"Operation published to peer GA")
                
        except Exception as e:
            log_message("GA", operation.get("id", "unknown"), operation.get("op", "UNKNOWN"), "error", 
                       f"Error publishing operation: {str(e)}")
    
    def _apply_remote_operation(self, operation: Dict) -> bool:
        """Apply operation received from remote GA"""
        try:
            operation_id = operation.get("id")
            op_type = operation.get("op")
            
            # Check idempotency
            if self.oplog.is_operation_applied(operation_id):
                log_message("GA", operation_id, op_type, "recibido", 
                           "Remote operation already applied, skipping (idempotency)")
                return False
            
            # Apply operation based on type
            if op_type == "RENOVAR":
                result = self.storage.renovar(
                    operation_id,
                    operation.get("codigo"),
                    operation.get("userId"),
                    operation.get("dueDateNew")
                )
            elif op_type == "DEVOLVER":
                result = self.storage.devolver(
                    operation_id,
                    operation.get("codigo"),
                    operation.get("userId")
                )
            elif op_type == "PRESTAR":
                result = self.storage.checkAndLoan(
                    operation_id,
                    operation.get("codigo"),
                    operation.get("userId")
                )
            else:
                log_message("GA", operation_id, op_type, "error", 
                           f"Unknown operation type: {op_type}")
                return False
            
            if result.get("ok", False):
                # Add to oplog (but don't re-publish to avoid loops)
                oplog_entry = {
                    "id": operation_id,
                    "op": op_type,
                    "codigo": operation.get("codigo"),
                    "userId": operation.get("userId"),
                    "dueDateNew": operation.get("dueDateNew"),
                    "ts": operation.get("ts"),
                    "remote": True,  # Mark as remote operation
                    "source_node": operation.get("source_node")
                }
                
                self.oplog.append_operation(oplog_entry)
                self.operations_received += 1
                
                log_message("GA", operation_id, op_type, "aplicado", 
                           f"Remote operation applied successfully")
                return True
            else:
                log_message("GA", operation_id, op_type, "error", 
                           f"Failed to apply remote operation: {result.get('reason')}")
                return False
                
        except Exception as e:
            log_message("GA", operation.get("id", "unknown"), operation.get("op", "UNKNOWN"), "error", 
                       f"Error applying remote operation: {str(e)}")
            return False
    
    def _subscription_loop(self):
        """Main loop for receiving operations from peer"""
        log_message("GA", "replication", "SUBSCRIBE", "recibido", 
                   "Starting subscription loop for remote operations")
        
        while self.running:
            try:
                if self.sub_socket.poll(1000):  # 1 second timeout
                    operation = self.sub_socket.recv_json()
                    self._apply_remote_operation(operation)
                else:
                    # Timeout, continue
                    continue
                    
            except zmq.Again:
                # Timeout, continue
                continue
            except Exception as e:
                log_message("GA", "replication", "SUBSCRIBE", "error", 
                           f"Error in subscription loop: {str(e)}")
                break
        
        log_message("GA", "replication", "SUBSCRIBE", "recibido", "Subscription loop stopped")
    
    def _check_snapshot_trigger(self):
        """Check if snapshot should be triggered"""
        current_ops = self.oplog.get_oplog_stats()["total_operations"]
        if current_ops - self.last_snapshot_ops >= self.snapshot_interval_ops:
            self._trigger_snapshot()
            self.last_snapshot_ops = current_ops
    
    def _trigger_snapshot(self):
        """Trigger snapshot creation for oplog truncation"""
        try:
            # For now, just truncate oplog to prevent it from growing indefinitely
            self.oplog.truncate_oplog(keep_last_n=1000)
            
            log_message("GA", "replication", "SNAPSHOT", "aplicado", 
                       "Snapshot triggered, oplog truncated")
            
        except Exception as e:
            log_message("GA", "replication", "SNAPSHOT", "error", 
                       f"Error creating snapshot: {str(e)}")
    
    def start(self):
        """Start replication service"""
        if self.running:
            return
        
        try:
            self._setup_sockets()
            self.running = True
            
            # Start subscription thread
            self.subscription_thread = threading.Thread(target=self._subscription_loop, daemon=True)
            self.subscription_thread.start()
            
            log_message("GA", "replication", "START", "recibido", 
                       f"Replication service started for node {self.node_id}")
            
        except Exception as e:
            log_message("GA", "replication", "START", "error", 
                       f"Error starting replication: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop replication service"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for threads to finish
        if self.subscription_thread and self.subscription_thread.is_alive():
            self.subscription_thread.join(timeout=2)
        
        # Close sockets
        if self.pub_socket:
            self.pub_socket.close()
        if self.sub_socket:
            self.sub_socket.close()
        if self.context:
            self.context.term()
        
        log_message("GA", "replication", "STOP", "recibido", 
                   f"Replication service stopped for node {self.node_id}")
    
    def replicate_operation(self, operation: Dict):
        """Replicate operation to peer GA"""
        if self.running and self.pub_socket:
            self._publish_operation(operation)
            self._check_snapshot_trigger()
    
    def get_replication_stats(self) -> Dict[str, Any]:
        """Get replication statistics"""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "operations_sent": self.operations_sent,
            "operations_received": self.operations_received,
            "snapshot_interval_ops": self.snapshot_interval_ops,
            "last_snapshot_ops": self.last_snapshot_ops
        }
