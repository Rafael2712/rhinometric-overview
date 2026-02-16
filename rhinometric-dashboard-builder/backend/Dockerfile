# RhinoMetric Dashboard Builder - Backend v2.2.0
FROM python:3.11-slim

LABEL maintainer="RhinoMetric Team"
LABEL version="2.2.0"
LABEL description="Visual dashboard builder for non-technical users"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ /app/app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8087

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8087/health').raise_for_status()"

# Run application
CMD ["python", "-m", "app.main"]
