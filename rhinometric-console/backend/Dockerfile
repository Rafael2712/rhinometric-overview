# Dockerfile para Rhinometric Console Backend
# Python 3.11 con FastAPI + Uvicorn

FROM python:3.11-slim

# Metadata
LABEL maintainer="Rhinometric Team"
LABEL version="2.5.0"
LABEL description="Rhinometric Console API Gateway - Backend Service"

# Configurar directorio de trabajo
WORKDIR /app

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema (si necesitas librerías nativas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 rhinometric && \
    chown -R rhinometric:rhinometric /app

USER rhinometric

# Exponer puerto
EXPOSE 8105

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8105/health || exit 1

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8105", "--workers", "1", "--log-level", "info"]
