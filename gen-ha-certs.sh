#!/bin/bash

# Crear directorio para los certificados
mkdir -p certs-ha
cd certs-ha

# Generar CA key y certificado
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=PrometheusHA-CA"

# Generar certificado de servidor para Prometheus
openssl genrsa -out prometheus-server.key 2048
openssl req -new -key prometheus-server.key -out prometheus-server.csr -subj "/CN=prometheus-server" \
    -addext "subjectAltName = DNS:prometheus-1,DNS:prometheus-2,DNS:localhost"
openssl x509 -req -days 365 -in prometheus-server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out prometheus-server.crt -extfile <(printf "subjectAltName=DNS:prometheus-1,DNS:prometheus-2,DNS:localhost")

# Generar certificado de cliente para HAProxy
openssl genrsa -out haproxy-client.key 2048
openssl req -new -key haproxy-client.key -out haproxy-client.csr -subj "/CN=haproxy-client"
openssl x509 -req -days 365 -in haproxy-client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out haproxy-client.crt

# Generar archivos PEM combinados
cat prometheus-server.key prometheus-server.crt > prometheus-server.pem
cat haproxy-client.key haproxy-client.crt > haproxy-client.pem

# Establecer permisos
chmod 644 *.crt *.pem
chmod 600 *.key *.csr

# Limpiar archivos CSR
rm *.csr

echo "Certificados generados exitosamente en el directorio certs-ha/"