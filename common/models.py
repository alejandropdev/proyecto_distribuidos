"""
Pydantic models for message schemas in the distributed library system.
All models follow the contract specifications exactly.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


class ClientRequest(BaseModel):
    """PS → GC request message"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sedeId: Literal["A", "B"]
    userId: str
    op: Literal["RENOVAR", "DEVOLVER", "PRESTAR"]
    libroCodigo: str
    timestamp: int


class GCReply(BaseModel):
    """GC → PS response message"""
    id: str
    status: Literal["RECIBIDO", "OK", "ERROR"]
    reason: Optional[str] = None
    dueDate: Optional[str] = None


class ActorMessage(BaseModel):
    """GC → AR/AD message via PUB/SUB"""
    id: str
    sedeId: str
    userId: str
    libroCodigo: str
    op: Literal["RENOVAR", "DEVOLVER"]
    dueDateNew: Optional[str] = None


class APRequest(BaseModel):
    """GC → AP request for PRESTAR operations"""
    id: str
    libroCodigo: str
    userId: str


class APReply(BaseModel):
    """AP → GC response"""
    ok: bool
    reason: Optional[str] = None
    metadata: Optional[dict] = None
