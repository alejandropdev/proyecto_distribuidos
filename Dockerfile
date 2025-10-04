# Dockerfile for Distributed Library System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p metrics data/ejemplos

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-m", "gestor_central.server", "--mode", "serial", "--mock-ap"]
