# ==========================================
# RHINOMETRIC v2.4.0 - API Connector Backend
# ==========================================

FROM python:3.11-slim

LABEL maintainer="RHINOMETRIC <contact@rhinometric.com>"
LABEL version="2.4.0"
LABEL description="FastAPI backend for visual datasource connector"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 rhinometric && \
    chown -R rhinometric:rhinometric /app

USER rhinometric

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
