FROM python:3.9-slim

# Instala dependencias
RUN pip install --no-cache-dir requests

# Crea directorio para logs
RUN mkdir -p /app/logs

# Copia el script
COPY test_ayuntamiento.py /app/test_ayuntamiento.py

# Define el directorio de trabajo
WORKDIR /app

# Comando para ejecutar el script
CMD ["python", "test_ayuntamiento.py"]
