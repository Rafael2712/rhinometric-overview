FROM python:3.11-slim

LABEL maintainer="rafael.canelon@rhinometric.com"
LABEL description="RHINOMETRIC VeriVerde - Sustainability & Energy Monitoring Exporter"
LABEL version="1.0"

WORKDIR /app

# No additional dependencies needed - using stdlib only
COPY exporter.py /app/

# Create non-root user
RUN useradd -m -u 1000 veriverde && \
    chown -R veriverde:veriverde /app

USER veriverde

EXPOSE 9200

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9200/health').read()"

CMD ["python", "-u", "exporter.py"]
