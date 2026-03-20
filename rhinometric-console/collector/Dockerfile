FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests psutil pyyaml

COPY config.py sender.py metrics.py logs.py traces.py utils.py main.py ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
