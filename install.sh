#!/bin/bash

echo "================================================"
echo "  Rhinometric Observability Platform Installer"
echo "================================================"

# Verificar requisitos
echo "Verificando requisitos del sistema..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    echo "   Instale Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    echo "   Instale Docker Compose desde: https://docs.docker.com/compose/install/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "   Instale Python3: sudo apt-get install python3"
    exit 1
fi

echo "✅ Todos los requisitos verificados"

# Solicitar información del cliente
echo ""
echo "CONFIGURACIÓN DE LICENCIA"
echo "========================="
echo "Tipos disponibles:"
echo "  1) Trial (30 días) - Evaluación gratuita"
echo "  2) Permanente - Pago único, sin expiración"
echo "  3) Anual - Suscripción con soporte incluido"
echo ""
read -p "Seleccione tipo de licencia [1-3]: " license_option

read -p "Nombre del cliente/ayuntamiento: " customer_name

# Generar licencia
echo ""
echo "Generando licencia..."

# Cambiar al directorio de scripts para generar la licencia
cd licensing/scripts

case $license_option in
    1)
        python3 license_generator.py trial "$customer_name" 30
        cd ../..
        cp licensing/scripts/license_${customer_name// /_}_trial.lic license.lic
        echo "✅ Licencia TRIAL generada (30 días)"
        ;;
    2)
        python3 license_generator.py permanent "$customer_name"
        cd ../..
        cp licensing/scripts/license_${customer_name// /_}_permanent.lic license.lic
        echo "✅ Licencia PERMANENTE generada"
        ;;
    3)
        python3 license_generator.py annual "$customer_name"
        cd ../..
        cp licensing/scripts/license_${customer_name// /_}_annual.lic license.lic
        echo "✅ Licencia ANUAL generada (365 días)"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

# Configurar servicios
echo ""
echo "Descargando componentes de la plataforma..."
docker-compose pull 2>/dev/null
echo "✅ Componentes descargados"

# Iniciar servicios
echo ""
echo "Iniciando plataforma..."
if [ -f "./start.sh" ]; then
    ./start.sh
else
    echo "Iniciando servicios directamente..."
    docker-compose up -d
fi

# Mostrar información de acceso
echo ""
echo "================================================"
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "================================================"
echo ""
echo "ACCESOS A LA PLATAFORMA:"
echo "------------------------"
echo "📊 Grafana (Dashboards):    http://localhost:3000"
echo "📈 Prometheus (Métricas):   http://localhost:9090"
echo "🌐 Aplicación Web:          http://localhost:8081"
echo "🔔 Alertmanager:            http://localhost:9093"
echo ""
echo "CREDENCIALES POR DEFECTO:"
echo "Usuario: admin"
echo "Password: admin"
echo ""
echo "DOCUMENTACIÓN:"
echo "https://github.com/rhinometric/docs"
echo ""
echo "SOPORTE:"
echo "Email: soporte@rhinometric.com"
echo "Tel: +34 900 XXX XXX"
echo ""
echo "Gracias por elegir Rhinometric"
echo "================================================"
