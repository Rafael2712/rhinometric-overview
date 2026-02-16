FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir schedule requests

# Copy backup script
COPY backup.py /app/

# Create backup directory
RUN mkdir -p /backups && \
    (useradd -m -u 1000 backup || true) && \
    chown -R backup:backup /app /backups

USER backup

# Healthcheck
HEALTHCHECK --interval=60s CMD python -c "import os; exit(0 if os.path.exists('/backups') else 1)"

CMD ["python", "-u", "backup.py"]
