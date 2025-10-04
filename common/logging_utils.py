"""
Standardized JSON logging utilities.
Provides both JSON and pretty (rich) logging formats.
"""

import json
import sys
from typing import Optional, Literal
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
import logging

from .time_utils import now_ms

# Rich console for pretty logging
console = Console()

# Process types
ProcessType = Literal["GC", "PS", "AR", "AD", "AP", "GA"]

# Operation types
OperationType = Literal["RENOVAR", "DEVOLVER", "PRESTAR"]

# Stage types
StageType = Literal["recibido", "enviado", "aplicado", "error"]


def json_log(
    proc: ProcessType,
    id: str,
    op: OperationType,
    stage: StageType,
    detail: str
) -> None:
    """
    Log a standardized JSON message to stdout.
    
    Args:
        proc: Process identifier (GC, PS, AR, AD, AP, GA)
        id: Unique request ID
        op: Operation type (RENOVAR, DEVOLVER, PRESTAR)
        stage: Processing stage (recibido, enviado, aplicado, error)
        detail: Additional detail text
    """
    log_entry = {
        "ts": now_ms(),
        "proc": proc,
        "id": id,
        "op": op,
        "stage": stage,
        "detail": detail
    }
    
    print(json.dumps(log_entry), flush=True)


def setup_pretty_logging(level: str = "INFO") -> None:
    """
    Setup rich logging for pretty console output.
    Call this when --pretty flag is used.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


def pretty_log(
    proc: ProcessType,
    id: str,
    op: OperationType,
    stage: StageType,
    detail: str
) -> None:
    """
    Log a pretty formatted message using rich.
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    console.print(
        f"[dim]{timestamp}[/dim] "
        f"[bold blue]{proc}[/bold blue] "
        f"[yellow]{id[:8]}[/yellow] "
        f"[green]{op}[/green] "
        f"[cyan]{stage}[/cyan] "
        f"{detail}"
    )


def log_message(
    proc: ProcessType,
    id: str,
    op: OperationType,
    stage: StageType,
    detail: str,
    pretty: bool = False
) -> None:
    """
    Unified logging function that chooses format based on pretty flag.
    """
    if pretty:
        pretty_log(proc, id, op, stage, detail)
    else:
        json_log(proc, id, op, stage, detail)
