"""
PS workload generator utilities.
Provides random delays and request validation for realistic load simulation.
"""

import random
import time
from typing import List, Dict, Any, Optional
from common.models import ClientRequest
from common.time_utils import now_ms


class WorkloadGenerator:
    """Generates realistic workload patterns for PS clients"""
    
    def __init__(self, min_delay_ms: int = 10, max_delay_ms: int = 50):
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
    
    def add_random_delay(self):
        """Add random delay between requests"""
        delay_ms = random.randint(self.min_delay_ms, self.max_delay_ms)
        time.sleep(delay_ms / 1000.0)
    
    def validate_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate request data and return error message if invalid.
        
        Args:
            request_data: Request data to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        # Check required fields
        required_fields = ["op", "libroCodigo", "userId"]
        for field in required_fields:
            if field not in request_data:
                return f"Missing required field: {field}"
        
        # Validate operation
        if request_data["op"] not in ["PRESTAR", "RENOVAR", "DEVOLVER"]:
            return f"Invalid operation: {request_data['op']}"
        
        # Validate libroCodigo format (basic check)
        libro_codigo = request_data["libroCodigo"]
        if not libro_codigo or len(libro_codigo) < 3:
            return f"Invalid libroCodigo: {libro_codigo}"
        
        # Validate userId format (basic check)
        user_id = request_data["userId"]
        if not user_id or not user_id.startswith("u-"):
            return f"Invalid userId format: {user_id}"
        
        return None
    
    def create_request(
        self, 
        sede_id: str, 
        request_data: Dict[str, Any]
    ) -> Optional[ClientRequest]:
        """
        Create a validated ClientRequest.
        
        Args:
            sede_id: Site ID (A or B)
            request_data: Request data
            
        Returns:
            ClientRequest if valid, None if invalid
        """
        # Validate request data
        error = self.validate_request(request_data)
        if error:
            return None
        
        try:
            return ClientRequest(
                sedeId=sede_id,
                userId=request_data["userId"],
                op=request_data["op"],
                libroCodigo=request_data["libroCodigo"],
                timestamp=now_ms()
            )
        except Exception as e:
            return None
    
    def generate_load_pattern(
        self, 
        requests: List[Dict[str, Any]], 
        duration_sec: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a load pattern for the given duration.
        
        Args:
            requests: Base request templates
            duration_sec: Duration in seconds
            
        Returns:
            List of requests to execute
        """
        if not requests:
            return []
        
        # Calculate how many requests we can fit in the duration
        # Assuming average delay between requests
        avg_delay_ms = (self.min_delay_ms + self.max_delay_ms) / 2
        requests_per_second = 1000 / avg_delay_ms
        total_requests = int(requests_per_second * duration_sec)
        
        # Generate request sequence
        workload = []
        for i in range(total_requests):
            # Select random request template
            template = random.choice(requests)
            workload.append(template.copy())
        
        return workload


def create_realistic_workload(
    base_requests: List[Dict[str, Any]],
    sites: List[str],
    duration_sec: int,
    requests_per_site_per_sec: float = 0.5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create realistic workload distribution across sites.
    
    Args:
        base_requests: Base request templates
        sites: List of site IDs
        duration_sec: Duration in seconds
        requests_per_site_per_sec: Requests per site per second
        
    Returns:
        Dictionary mapping site_id to list of requests
    """
    workload_by_site = {}
    
    for site in sites:
        # Calculate requests for this site
        total_requests = int(requests_per_site_per_sec * duration_sec)
        
        # Generate requests for this site
        site_requests = []
        for _ in range(total_requests):
            template = random.choice(base_requests)
            site_requests.append(template.copy())
        
        workload_by_site[site] = site_requests
    
    return workload_by_site
