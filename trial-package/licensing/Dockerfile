FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    PyJWT==2.8.0 \
    flask-cors==4.0.0

# Crear directorios
RUN mkdir -p /data && chmod 755 /data

# Copiar servidor de licencias
COPY license_server.py /app/

# Variables de entorno
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Iniciar
CMD ["python", "-u", "license_server.py"]
