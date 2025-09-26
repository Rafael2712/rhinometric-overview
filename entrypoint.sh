#!/bin/sh

echo "Iniciando validador Flask..."

# Ejecuta el validador
python3 /validator/main.py

# Evita que el contenedor se cierre si el proceso termina
tail -f /dev/null
