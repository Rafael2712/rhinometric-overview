FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    numpy==1.26.0 \
    scikit-learn==1.3.2 \
    requests==2.31.0 \
    prometheus-client==0.19.0

# Copy detector script
COPY detector.py /app/

# Create non-root user
RUN useradd -m -u 1000 anomaly && \
    chown -R anomaly:anomaly /app

USER anomaly

EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["python", "-u", "detector.py"]
