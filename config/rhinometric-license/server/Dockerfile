FROM python:3.9-slim
WORKDIR /app
RUN pip install flask pyjwt
COPY license_server.py .
CMD ["python", "license_server.py"]
