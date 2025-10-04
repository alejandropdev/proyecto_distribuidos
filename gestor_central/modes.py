"""
GC execution modes: serial and threaded.
Implements different concurrency strategies for handling PS requests.
"""

import json
import zmq
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from common.env import GC_BIND, GC_PUB_BIND, AP_REQ_CONNECT
from common.logging_utils import log_message
from .router import GCRouter


class GCMode:
    """Base class for GC execution modes"""
    
    def __init__(self, pretty: bool = False, mock_ap: bool = False):
        self.pretty = pretty
        self.mock_ap = mock_ap
        self.context = zmq.Context()
        self.running = False
        
        # Setup sockets
        self.rep_socket = self.context.socket(zmq.REP)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.ap_socket = self.context.socket(zmq.REQ)
        
        # Bind sockets
        self.rep_socket.bind(GC_BIND)
        self.pub_socket.bind(GC_PUB_BIND)
        if not mock_ap:
            self.ap_socket.connect(AP_REQ_CONNECT)
        
        # Create router
        self.router = GCRouter(self.pub_socket, self.ap_socket, pretty, mock_ap)
        
        log_message(
            "GC", "startup", "INIT", "recibido",
            f"GC started, listening on {GC_BIND}, publishing on {GC_PUB_BIND}",
            pretty
        )
    
    def start(self):
        """Start the GC server"""
        self.running = True
        self._run()
    
    def stop(self):
        """Stop the GC server"""
        self.running = False
        self.rep_socket.close()
        self.pub_socket.close()
        self.ap_socket.close()
        self.context.term()
    
    def _run(self):
        """Override in subclasses"""
        raise NotImplementedError


class SerialMode(GCMode):
    """Serial mode: handles one request at a time"""
    
    def _run(self):
        """Serial processing loop"""
        log_message(
            "GC", "serial", "INIT", "recibido",
            "Starting serial mode",
            self.pretty
        )
        
        while self.running:
            try:
                # Receive request
                request_data = self.rep_socket.recv_string()
                
                # Process request
                response_data = self.router.handle_request(json.loads(request_data))
                
                # Send response
                self.rep_socket.send_string(json.dumps(response_data))
                
            except zmq.Again:
                # No message available, continue
                continue
            except Exception as e:
                log_message(
                    "GC", "serial", "ERROR", "error",
                    f"Serial processing error: {str(e)}",
                    self.pretty
                )
                # Send error response
                try:
                    error_response = {"id": "unknown", "status": "ERROR", "reason": str(e)}
                    self.rep_socket.send_string(json.dumps(error_response))
                except:
                    pass


class ThreadedMode(GCMode):
    """Threaded mode: uses thread pool for concurrent request handling"""
    
    def __init__(self, workers: int = 8, pretty: bool = False, mock_ap: bool = False):
        super().__init__(pretty, mock_ap)
        self.workers = workers
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.response_lock = threading.Lock()
    
    def _run(self):
        """Threaded processing loop"""
        log_message(
            "GC", "threaded", "INIT", "recibido",
            f"Starting threaded mode with {self.workers} workers",
            self.pretty
        )
        
        while self.running:
            try:
                # Receive request
                request_data = self.rep_socket.recv_string()
                
                # Submit to thread pool
                future = self.executor.submit(self._process_request, request_data)
                
                # Wait for result and send response
                response_data = future.result()
                self.rep_socket.send_string(json.dumps(response_data))
                
            except zmq.Again:
                # No message available, continue
                continue
            except Exception as e:
                log_message(
                    "GC", "threaded", "ERROR", "error",
                    f"Threaded processing error: {str(e)}",
                    self.pretty
                )
                # Send error response
                try:
                    error_response = {"id": "unknown", "status": "ERROR", "reason": str(e)}
                    self.rep_socket.send_string(json.dumps(error_response))
                except:
                    pass
    
    def _process_request(self, request_data: str) -> Dict[str, Any]:
        """Process request in thread pool"""
        try:
            return self.router.handle_request(json.loads(request_data))
        except Exception as e:
            log_message(
                "GC", "threaded", "ERROR", "error",
                f"Thread processing error: {str(e)}",
                self.pretty
            )
            return {"id": "unknown", "status": "ERROR", "reason": str(e)}
    
    def stop(self):
        """Stop threaded mode"""
        self.executor.shutdown(wait=True)
        super().stop()


def create_gc_mode(mode: str, workers: int = 8, pretty: bool = False, mock_ap: bool = False) -> GCMode:
    """
    Factory function to create GC mode instance.
    
    Args:
        mode: "serial" or "threaded"
        workers: Number of worker threads (for threaded mode)
        pretty: Enable pretty logging
        mock_ap: Use mock AP responses
        
    Returns:
        GCMode instance
    """
    if mode == "serial":
        return SerialMode(pretty, mock_ap)
    elif mode == "threaded":
        return ThreadedMode(workers, pretty, mock_ap)
    else:
        raise ValueError(f"Unknown GC mode: {mode}")
