FROM python:3.11-slim

WORKDIR /workspace

# Install dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (preserves app/ as package directory)
COPY app/ /workspace/app/
COPY config.yaml /workspace/
COPY alert_mappings.yaml /workspace/

# Set Python path to include /workspace
ENV PYTHONPATH=/workspace

# Create non-root user
RUN useradd -m -u 1000 anomaly && \
    chown -R anomaly:anomaly /workspace

USER anomaly

EXPOSE 8085

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8085/health', timeout=3)" || exit 1

CMD ["python", "-u", "app/main.py"]
