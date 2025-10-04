"""
GC routing logic for different operations.
Handles RENOVAR, DEVOLVER, and PRESTAR operations according to contract.
"""

import json
import zmq
from typing import Dict, Any
from common.models import ClientRequest, GCReply, ActorMessage, APRequest, APReply
from common.logging_utils import log_message
from common.time_utils import today_plus_days
from common.env import TOPIC_RENOVACION, TOPIC_DEVOLUCION, AP_REQ_CONNECT


class GCRouter:
    """Handles routing logic for GC operations"""
    
    def __init__(self, pub_socket: zmq.Socket, ap_socket: zmq.Socket, pretty: bool = False, mock_ap: bool = False):
        self.pub_socket = pub_socket
        self.ap_socket = ap_socket
        self.pretty = pretty
        self.mock_ap = mock_ap
        
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a client request to the appropriate handler.
        
        Args:
            request_data: Parsed JSON request data
            
        Returns:
            Response data to send back to PS
        """
        try:
            # Validate and parse request
            request = ClientRequest(**request_data)
            
            log_message(
                "GC", request.id, request.op, "recibido",
                f"Request from sede {request.sedeId}, user {request.userId}",
                self.pretty
            )
            
            # Route based on operation
            if request.op == "RENOVAR":
                return self._handle_renovar(request)
            elif request.op == "DEVOLVER":
                return self._handle_devolver(request)
            elif request.op == "PRESTAR":
                return self._handle_prestar(request)
            else:
                return self._error_response(request.id, f"Unknown operation: {request.op}")
                
        except Exception as e:
            # Handle validation errors or other exceptions
            request_id = request_data.get("id", "unknown")
            log_message(
                "GC", request_id, "UNKNOWN", "error",
                f"Request validation failed: {str(e)}",
                self.pretty
            )
            return self._error_response(request_id, f"Invalid request: {str(e)}")
    
    def _handle_renovar(self, request: ClientRequest) -> Dict[str, Any]:
        """Handle RENOVAR operation"""
        # Calculate new due date (7 days from now)
        due_date_new = today_plus_days(7)
        
        # Create actor message
        actor_msg = ActorMessage(
            id=request.id,
            sedeId=request.sedeId,
            userId=request.userId,
            libroCodigo=request.libroCodigo,
            op="RENOVAR",
            dueDateNew=due_date_new
        )
        
        # Publish to RENOVACION topic
        topic_msg = f"{TOPIC_RENOVACION} {json.dumps(actor_msg.model_dump())}"
        self.pub_socket.send_string(topic_msg)
        
        log_message(
            "GC", request.id, "RENOVAR", "enviado",
            f"Published to topic {TOPIC_RENOVACION}",
            self.pretty
        )
        
        # Return immediate confirmation
        return GCReply(id=request.id, status="RECIBIDO").model_dump()
    
    def _handle_devolver(self, request: ClientRequest) -> Dict[str, Any]:
        """Handle DEVOLVER operation"""
        # Create actor message
        actor_msg = ActorMessage(
            id=request.id,
            sedeId=request.sedeId,
            userId=request.userId,
            libroCodigo=request.libroCodigo,
            op="DEVOLVER"
        )
        
        # Publish to DEVOLUCION topic
        topic_msg = f"{TOPIC_DEVOLUCION} {json.dumps(actor_msg.model_dump())}"
        self.pub_socket.send_string(topic_msg)
        
        log_message(
            "GC", request.id, "DEVOLVER", "enviado",
            f"Published to topic {TOPIC_DEVOLUCION}",
            self.pretty
        )
        
        # Return immediate confirmation
        return GCReply(id=request.id, status="RECIBIDO").model_dump()
    
    def _handle_prestar(self, request: ClientRequest) -> Dict[str, Any]:
        """Handle PRESTAR operation - requires round-trip with AP"""
        try:
            if self.mock_ap:
                # Mock AP response for testing
                log_message(
                    "GC", request.id, "PRESTAR", "enviado",
                    f"Using mock AP response",
                    self.pretty
                )
                
                # Simulate AP response
                due_date = today_plus_days(14)  # 14 days from now
                
                log_message(
                    "GC", request.id, "PRESTAR", "aplicado",
                    f"Mock AP response: ok=True, dueDate={due_date}",
                    self.pretty
                )
                
                return GCReply(
                    id=request.id,
                    status="OK",
                    dueDate=due_date
                ).model_dump()
            else:
                # Real AP communication
                # Create AP request
                ap_request = APRequest(
                    id=request.id,
                    libroCodigo=request.libroCodigo,
                    userId=request.userId
                )
                
                # Send request to AP
                self.ap_socket.send_string(json.dumps(ap_request.model_dump()))
                
                log_message(
                    "GC", request.id, "PRESTAR", "enviado",
                    f"Sent request to AP",
                    self.pretty
                )
                
                # Wait for response from AP
                response_data = self.ap_socket.recv_string()
                ap_reply = APReply(**json.loads(response_data))
                
                log_message(
                    "GC", request.id, "PRESTAR", "aplicado",
                    f"Received response from AP: ok={ap_reply.ok}",
                    self.pretty
                )
                
                # Map AP response to GC response
                if ap_reply.ok:
                    due_date = None
                    if ap_reply.metadata and "dueDate" in ap_reply.metadata:
                        due_date = ap_reply.metadata["dueDate"]
                    
                    return GCReply(
                        id=request.id,
                        status="OK",
                        dueDate=due_date
                    ).model_dump()
                else:
                    return GCReply(
                        id=request.id,
                        status="ERROR",
                        reason=ap_reply.reason
                    ).model_dump()
                
        except Exception as e:
            log_message(
                "GC", request.id, "PRESTAR", "error",
                f"AP communication failed: {str(e)}",
                self.pretty
            )
            return self._error_response(request.id, f"AP communication failed: {str(e)}")
    
    def _error_response(self, request_id: str, reason: str) -> Dict[str, Any]:
        """Create error response"""
        return GCReply(
            id=request_id,
            status="ERROR",
            reason=reason
        ).model_dump()
