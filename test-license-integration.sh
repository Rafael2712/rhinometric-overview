#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  RHINOMETRIC v2.3.0 - LICENSE INTEGRATION TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# TEST 1: Validate license file exists
# ============================================================================

echo "TEST 1: Validando archivo de licencia..."

if [ -f "licenses/cliente.lic" ]; then
    echo "✅ Archivo de licencia encontrado: licenses/cliente.lic"
    echo "   Tamaño: $(du -h licenses/cliente.lic | cut -f1)"
else
    echo "❌ ERROR: Archivo de licencia NO encontrado"
    exit 1
fi

echo ""

# ============================================================================
# TEST 2: Validate public key exists
# ============================================================================

echo "TEST 2: Validando clave pública..."

if [ -f "security/rhinometric_public.pem" ]; then
    echo "✅ Clave pública encontrada: security/rhinometric_public.pem"
    echo "   Tamaño: $(du -h security/rhinometric_public.pem | cut -f1)"
else
    echo "❌ ERROR: Clave pública NO encontrada"
    exit 1
fi

echo ""

# ============================================================================
# TEST 3: Validate license with Python script
# ============================================================================

echo "TEST 3: Validando licencia con Python..."

if [ -f "security/validate_license.py" ]; then
    echo "✅ Script de validación encontrado"
    
    # Try to validate
    python3 security/validate_license.py "TestService"
    VALIDATION_RESULT=$?
    
    if [ $VALIDATION_RESULT -eq 0 ]; then
        echo "✅ Validación exitosa"
    else
        echo "❌ Validación falló (código: $VALIDATION_RESULT)"
        exit 1
    fi
else
    echo "❌ ERROR: Script de validación NO encontrado"
    exit 1
fi

echo ""

# ============================================================================
# TEST 4: Validate entrypoint scripts exist
# ============================================================================

echo "TEST 4: Validando entrypoints..."

for service in grafana prometheus loki; do
    script="entrypoint-${service}-licensed.sh"
    if [ -f "$script" ]; then
        echo "✅ $script encontrado"
        if [ -x "$script" ]; then
            echo "   └─ Permisos de ejecución: OK"
        else
            echo "   └─ ⚠️  Sin permisos de ejecución"
        fi
    else
        echo "❌ $script NO encontrado"
        exit 1
    fi
done

echo ""

# ============================================================================
# TEST 5: Check Docker Compose configuration
# ============================================================================

echo "TEST 5: Validando docker-compose..."

if docker compose -f docker-compose-v2.2.0.yml config > /dev/null 2>&1; then
    echo "✅ Configuración de docker-compose válida"
else
    echo "❌ ERROR: Configuración de docker-compose inválida"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ TODOS LOS TESTS PASARON"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Próximos pasos:"
echo "  1. docker compose -f docker-compose-v2.2.0.yml up -d grafana"
echo "  2. docker logs rhinometric-grafana -f"
echo ""
