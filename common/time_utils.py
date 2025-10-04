"""
Time utilities for the distributed library system.
Provides millisecond timestamps and date formatting.
"""

import time
from datetime import datetime, timedelta
from typing import Optional


def now_ms() -> int:
    """Get current timestamp in milliseconds since epoch"""
    return int(time.time() * 1000)


def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def add_days_to_date(date_str: str, days: int) -> str:
    """
    Add days to a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        days: Number of days to add
        
    Returns:
        New date in YYYY-MM-DD format
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date = date_obj + timedelta(days=days)
        return new_date.strftime("%Y-%m-%d")
    except ValueError:
        # If parsing fails, return today + days
        today = datetime.now()
        new_date = today + timedelta(days=days)
        return new_date.strftime("%Y-%m-%d")


def today_plus_days(days: int) -> str:
    """
    Get today's date plus specified days in YYYY-MM-DD format.
    
    Args:
        days: Number of days to add to today
        
    Returns:
        Date in YYYY-MM-DD format
    """
    today = datetime.now()
    future_date = today + timedelta(days=days)
    return future_date.strftime("%Y-%m-%d")


def format_timestamp_ms(timestamp_ms: int) -> str:
    """
    Format a millisecond timestamp as readable string.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        Formatted timestamp string
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
