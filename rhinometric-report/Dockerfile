FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PDF generation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    fontconfig \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb || apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    jinja2==3.1.2 \
    requests==2.31.0 \
    pdfkit==1.0.0 \
    schedule==1.2.0

# Copy application files
COPY reporter.py /app/
COPY template.html /app/

# Create non-root user
RUN useradd -m -u 1000 reports && \
    chown -R reports:reports /app

USER reports

# Healthcheck
HEALTHCHECK --interval=60s CMD python -c "import os; exit(0)"

CMD ["python", "-u", "reporter.py"]
