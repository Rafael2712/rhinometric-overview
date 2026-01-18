# RhinoMetric Report Generator v2.2.0
FROM python:3.11-slim

LABEL maintainer="RhinoMetric Team"
LABEL version="2.2.0"
LABEL description="Enterprise-grade PDF/HTML report generation and email delivery"

# Set working directory
WORKDIR /app

# Install system dependencies for WeasyPrint and ReportLab
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/
COPY templates/ /app/templates/
COPY config.yaml /app/config.yaml
COPY tracing.py /app/tracing.py

# Create directories
RUN mkdir -p /app/reports /app/temp /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8086

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8086/health').raise_for_status()"

# Run application
CMD ["python", "-m", "app.main"]
