"""
Environment configuration loader with defaults.
Loads .env file and provides typed access to configuration values.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value


def get_env_optional(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get optional environment variable"""
    return os.getenv(key, default)


# GC Configuration
GC_BIND = get_env("GC_BIND", "tcp://0.0.0.0:5555")
GC_PUB_BIND = get_env("GC_PUB_BIND", "tcp://0.0.0.0:5556")
TOPIC_RENOVACION = get_env("TOPIC_RENOVACION", "RENOVACION")
TOPIC_DEVOLUCION = get_env("TOPIC_DEVOLUCION", "DEVOLUCION")

# Actor connections
GC_PUB_CONNECT = get_env_optional("GC_PUB_CONNECT", "tcp://127.0.0.1:5556")

# AP connection
AP_REQ_CONNECT = get_env("AP_REQ_CONNECT", "tcp://127.0.0.1:5557")

# GC Mode
GC_MODE = get_env("GC_MODE", "serial")

# Metrics
METRICS_CSV = get_env("METRICS_CSV", "metrics/results.csv")
MEASUREMENT_WINDOW_SEC = int(get_env("MEASUREMENT_WINDOW_SEC", "120"))
