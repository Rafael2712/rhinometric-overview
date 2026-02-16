#!/bin/bash
set -e

echo "🔐 Validando licencia..."
python3 /app/validator.py /license/license.lic || exit 1

echo "✅ Licencia válida"
echo "🚀 Plataforma iniciada (modo demo)"

# Mantener contenedor vivo
tail -f /dev/null
