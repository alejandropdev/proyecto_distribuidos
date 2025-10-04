FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y datos
COPY . .

# Crear directorio para datos si no existe
RUN mkdir -p data

# Hacer ejecutables los scripts de Python
RUN chmod +x *.py

# Comando por defecto (será sobrescrito en docker-compose.yml)
CMD ["python", "gestor_carga.py"]
