"""
GA Oplog module - Handles append-only operation log for replication.
Provides incremental reading and idempotency guarantees.
"""

import os
import json
import threading
from typing import Dict, List, Optional, Set
from datetime import datetime

from common.time_utils import now_ms
from common.logging_utils import log_message


class GAOplog:
    """Append-only operation log with idempotency support"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.oplog_file = os.path.join(data_dir, "oplog.json")
        self.applied_index_file = os.path.join(data_dir, "applied_index.json")
        self._lock = threading.RLock()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        # Load applied operations set for idempotency
        self._applied_operations: Set[str] = self._load_applied_operations()
    
    def _initialize_files(self):
        """Initialize oplog and applied index files if they don't exist"""
        with self._lock:
            if not os.path.exists(self.oplog_file):
                self._write_json_file(self.oplog_file, [])
            
            if not os.path.exists(self.applied_index_file):
                self._write_json_file(self.applied_index_file, {
                    "last_applied_index": -1,
                    "applied_operations": []
                })
    
    def _read_json_file(self, filepath: str) -> any:
        """Read JSON file safely"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return [] if "oplog" in filepath else {}
        except (json.JSONDecodeError, IOError) as e:
            log_message("GA", "oplog", "READ", "error", f"Error reading {filepath}: {str(e)}")
            return [] if "oplog" in filepath else {}
    
    def _write_json_file(self, filepath: str, data: any):
        """Write JSON file atomically"""
        try:
            # Write to temporary file first
            temp_file = filepath + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_file, filepath)
        except IOError as e:
            log_message("GA", "oplog", "WRITE", "error", f"Error writing {filepath}: {str(e)}")
            raise
    
    def _load_applied_operations(self) -> Set[str]:
        """Load set of applied operation IDs for idempotency"""
        applied_index = self._read_json_file(self.applied_index_file)
        applied_ops = applied_index.get("applied_operations", [])
        return set(applied_ops)
    
    def _save_applied_operations(self, operation_id: str):
        """Save applied operation ID to index"""
        applied_index = self._read_json_file(self.applied_index_file)
        applied_ops = applied_index.get("applied_operations", [])
        
        if operation_id not in applied_ops:
            applied_ops.append(operation_id)
            applied_index["applied_operations"] = applied_ops
            applied_index["last_applied_index"] = len(applied_ops) - 1
            self._write_json_file(self.applied_index_file, applied_index)
    
    def append_operation(self, operation: Dict) -> bool:
        """
        Append operation to oplog.
        Returns True if operation was appended, False if already exists (idempotency).
        """
        with self._lock:
            operation_id = operation.get("id")
            
            # Check idempotency
            if operation_id in self._applied_operations:
                log_message("GA", operation_id, operation.get("op", "UNKNOWN"), "recibido", 
                           "Operation already applied, skipping (idempotency)")
                return False
            
            # Add timestamp if not present
            if "ts" not in operation:
                operation["ts"] = now_ms()
            
            # Read current oplog
            oplog = self._read_json_file(self.oplog_file)
            
            # Append operation
            oplog.append(operation)
            
            # Write back
            self._write_json_file(self.oplog_file, oplog)
            
            # Mark as applied
            self._applied_operations.add(operation_id)
            self._save_applied_operations(operation_id)
            
            log_message("GA", operation_id, operation.get("op", "UNKNOWN"), "aplicado", 
                       f"Operation appended to oplog")
            
            return True
    
    def get_operations_since(self, last_index: int) -> List[Dict]:
        """
        Get operations since the given index.
        Used for incremental replication.
        """
        with self._lock:
            oplog = self._read_json_file(self.oplog_file)
            return oplog[last_index + 1:]
    
    def get_all_operations(self) -> List[Dict]:
        """Get all operations from oplog"""
        with self._lock:
            return self._read_json_file(self.oplog_file)
    
    def get_last_applied_index(self) -> int:
        """Get the last applied operation index"""
        with self._lock:
            applied_index = self._read_json_file(self.applied_index_file)
            return applied_index.get("last_applied_index", -1)
    
    def is_operation_applied(self, operation_id: str) -> bool:
        """Check if operation was already applied (idempotency check)"""
        with self._lock:
            return operation_id in self._applied_operations
    
    def truncate_oplog(self, keep_last_n: int = 1000):
        """
        Truncate oplog keeping only the last N operations.
        Used for maintenance to prevent oplog from growing indefinitely.
        """
        with self._lock:
            oplog = self._read_json_file(self.oplog_file)
            
            if len(oplog) <= keep_last_n:
                return  # Nothing to truncate
            
            # Keep last N operations
            truncated_oplog = oplog[-keep_last_n:]
            
            # Update applied operations set
            truncated_ids = {op.get("id") for op in truncated_oplog}
            self._applied_operations = truncated_ids
            
            # Write truncated oplog
            self._write_json_file(self.oplog_file, truncated_oplog)
            
            # Update applied index
            applied_index = {
                "last_applied_index": len(truncated_oplog) - 1,
                "applied_operations": list(truncated_ids)
            }
            self._write_json_file(self.applied_index_file, applied_index)
            
            log_message("GA", "maintenance", "TRUNCATE", "aplicado", 
                       f"Oplog truncated to last {keep_last_n} operations")
    
    def get_oplog_stats(self) -> Dict:
        """Get oplog statistics"""
        with self._lock:
            oplog = self._read_json_file(self.oplog_file)
            applied_index = self._read_json_file(self.applied_index_file)
            
            return {
                "total_operations": len(oplog),
                "applied_operations": len(self._applied_operations),
                "last_applied_index": applied_index.get("last_applied_index", -1),
                "oplog_size_bytes": os.path.getsize(self.oplog_file) if os.path.exists(self.oplog_file) else 0
            }
