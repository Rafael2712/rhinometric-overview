#!/bin/bash

# Directorio para certificados
CERT_DIR="./certs"
mkdir -p $CERT_DIR

# Generar CA privada
openssl genrsa -out $CERT_DIR/ca.key 4096

# Generar certificado CA
openssl req -new -x509 -key $CERT_DIR/ca.key -out $CERT_DIR/ca.crt -days 365 -subj "/CN=RhinometricCA"

# Función para generar certificados para cada servicio
generate_service_cert() {
    SERVICE=$1
    
    # Generar llave privada
    openssl genrsa -out $CERT_DIR/$SERVICE.key 2048
    
    # Generar CSR
    openssl req -new -key $CERT_DIR/$SERVICE.key -out $CERT_DIR/$SERVICE.csr -subj "/CN=$SERVICE"
    
    # Firmar certificado
    openssl x509 -req -in $CERT_DIR/$SERVICE.csr -CA $CERT_DIR/ca.crt -CAkey $CERT_DIR/ca.key \
        -CAcreateserial -out $CERT_DIR/$SERVICE.crt -days 365
    
    # Limpiar CSR
    rm $CERT_DIR/$SERVICE.csr
    
    # Configurar permisos
    chmod 644 $CERT_DIR/$SERVICE.crt
    chmod 600 $CERT_DIR/$SERVICE.key
}

# Generar certificados para cada servicio
generate_service_cert "prometheus"
generate_service_cert "grafana"
generate_service_cert "loki"
generate_service_cert "pushgateway"

echo "Certificados generados exitosamente en $CERT_DIR"