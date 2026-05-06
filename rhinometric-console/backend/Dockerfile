FROM python:3.11-slim
LABEL version=2.6.3-p0retention
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 rhinometric && chown -R rhinometric:rhinometric /app
USER rhinometric
EXPOSE 8105
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD curl -f http://localhost:8105/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8105", "--workers", "1", "--log-level", "info"]