FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc &&     pip install --upgrade pip &&     pip install flask pyjwt

COPY license_server.py .

CMD ["python", "license_server.py"]
