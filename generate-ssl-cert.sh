#!/bin/bash

# Generar llave privada y certificado autofirmado
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"

# Combinar certificado y llave en un solo archivo PEM
cat cert.pem key.pem > server.pem

# Crear directorio de certificados si no existe
mkdir -p certs

# Mover archivos a ubicación final
mv server.pem certs/
mv cert.pem certs/
mv key.pem certs/

echo "Certificados generados en el directorio certs/"