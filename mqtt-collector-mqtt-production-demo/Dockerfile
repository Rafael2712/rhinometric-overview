FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector code
COPY collector.py .

# Expose metrics port
EXPOSE 9320

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9320/metrics')" || exit 1

# Run collector
CMD ["python", "-u", "collector.py"]
