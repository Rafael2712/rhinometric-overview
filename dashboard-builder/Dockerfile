FROM python:3.11-slim

LABEL maintainer="RHINOMETRIC v2.4.0"
LABEL description="Dashboard Builder Backend - Visual dashboard creator for Grafana"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY models.py .
COPY templates/ ./templates/

# Non-root user
RUN useradd -m -u 1000 rhinometric && chown -R rhinometric:rhinometric /app
USER rhinometric

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/')" || exit 1

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]
