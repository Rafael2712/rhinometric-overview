FROM python:3.11-slim

LABEL maintainer="Rhinometric <support@rhinometric.com>"
LABEL description="Rhinometric Telemetry Collector"
LABEL version="1.2.0"

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir requests psutil pyyaml

# Copy collector source
COPY config.py sender.py metrics.py logs.py traces.py utils.py main.py ./

# Ensure unbuffered stdout for Docker logs
ENV PYTHONUNBUFFERED=1

# Default config (can be overridden)
ENV COLLECT_INTERVAL=15
ENV ENABLE_METRICS=true
ENV ENABLE_LOGS=true
ENV ENABLE_TRACES=true
ENV LOG_LEVEL=INFO

# Health check: process must be running
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import psutil; assert any(p.info['name']=='python3' or 'main.py' in ' '.join(p.info.get('cmdline') or []) for p in psutil.process_iter(['name','cmdline']))" || exit 1

CMD ["python", "main.py"]
