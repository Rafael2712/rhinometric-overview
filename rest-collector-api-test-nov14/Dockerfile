FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector code
COPY collector.py .

# Expose metrics port
EXPOSE 9307

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9307/metrics')" || exit 1

# Run collector
CMD ["python", "-u", "collector.py"]
