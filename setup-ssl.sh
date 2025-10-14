#!/bin/bash

# Generar contraseña para autenticación básica
echo "Generando credenciales para autenticación básica..."
mkdir -p nginx
htpasswd -c nginx/.htpasswd admin

# Crear directorios necesarios
mkdir -p nginx/certs
mkdir -p certbot/www

# Generar certificado autofirmado temporal
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem \
  -subj "/C=ES/ST=Madrid/L=Madrid/O=RhinoMetric/CN=localhost"

echo "Configuración SSL inicial completada."
echo "IMPORTANTE: Para producción, reemplazar el certificado autofirmado con un certificado válido de Let's Encrypt."