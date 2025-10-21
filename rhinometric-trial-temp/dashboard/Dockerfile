FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    flask-cors==4.0.0

# Copiar aplicación
COPY app.py /app/
COPY templates/ /app/templates/

# Variables de entorno
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV DASHBOARD_PORT=8080

# Puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Iniciar
CMD ["python", "app.py"]
