FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir \
    requests==2.31.0 \
    flask==2.3.3 \
    PyJWT==2.8.0 \
    cryptography==41.0.7 \
    psycopg2-binary==2.9.7 \
    flask-cors==4.0.0

# Crear directorios necesarios
RUN mkdir -p /app/logs /data /app/licenses && \
    chmod 755 /app/logs /data /app/licenses

# Copiar script del servidor de licencias
COPY license_server.py /app/license_server.py

# Variables de entorno
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Puerto del servidor
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Iniciar servidor
CMD ["python", "-u", "license_server.py"]
