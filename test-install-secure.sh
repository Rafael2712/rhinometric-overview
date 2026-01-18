#!/usr/bin/env bash

################################################################################
#                                                                              #
#          RHINOMETRIC v2.3.0 - TEST SUITE PARA INSTALL-SECURE.SH             #
#                                                                              #
#  Script de testing que simula el instalador sin realizar cambios reales     #
#                                                                              #
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS=()

# Colores
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'

print_header() {
    echo ""
    echo -e "${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_CYAN}  $1${COLOR_RESET}"
    echo -e "${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
    echo ""
}

test_result() {
    local test_name="$1"
    local result="$2"
    
    if [[ "$result" == "PASS" ]]; then
        echo -e "${COLOR_GREEN}✓${COLOR_RESET} ${test_name}: ${COLOR_GREEN}PASS${COLOR_RESET}"
        TEST_RESULTS+=("PASS:${test_name}")
    else
        echo -e "${COLOR_RED}✗${COLOR_RESET} ${test_name}: ${COLOR_RED}FAIL${COLOR_RESET}"
        TEST_RESULTS+=("FAIL:${test_name}")
    fi
}

print_header "TEST SUITE - INSTALL-SECURE.SH"

echo "Ejecutando tests de verificación..."
echo ""

# Test 1: Verificar que el script existe
print_header "Test 1: Existencia del script"

if [[ -f "${SCRIPT_DIR}/install-secure.sh" ]]; then
    test_result "Script install-secure.sh existe" "PASS"
else
    test_result "Script install-secure.sh existe" "FAIL"
fi

# Test 2: Verificar permisos de ejecución
if [[ -x "${SCRIPT_DIR}/install-secure.sh" ]]; then
    test_result "Permisos de ejecución" "PASS"
else
    test_result "Permisos de ejecución" "FAIL"
fi

# Test 3: Verificar sintaxis bash
print_header "Test 2: Sintaxis Bash"

if bash -n "${SCRIPT_DIR}/install-secure.sh" 2>/dev/null; then
    test_result "Sintaxis bash correcta" "PASS"
else
    test_result "Sintaxis bash correcta" "FAIL"
fi

# Test 4: Verificar variables críticas definidas
print_header "Test 3: Variables críticas"

CRITICAL_VARS=(
    "VERSION"
    "COMPOSE_FILE"
    "LICENSE_FILE"
    "VALIDATOR_SCRIPT"
    "CRITICAL_PORTS"
)

for var in "${CRITICAL_VARS[@]}"; do
    if grep -q "^${var}=" "${SCRIPT_DIR}/install-secure.sh"; then
        test_result "Variable ${var} definida" "PASS"
    else
        test_result "Variable ${var} definida" "FAIL"
    fi
done

# Test 5: Verificar funciones críticas
print_header "Test 4: Funciones críticas"

CRITICAL_FUNCTIONS=(
    "detect_os"
    "validate_license"
    "check_dependencies"
    "check_ports"
    "create_backup"
    "deploy_stack"
    "verify_deployment"
    "rollback_installation"
)

for func in "${CRITICAL_FUNCTIONS[@]}"; do
    if grep -q "^${func}()" "${SCRIPT_DIR}/install-secure.sh"; then
        test_result "Función ${func}() presente" "PASS"
    else
        test_result "Función ${func}() presente" "FAIL"
    fi
done

# Test 6: Verificar trap para cleanup
print_header "Test 5: Manejo de errores"

if grep -q "trap cleanup_on_exit" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Trap para cleanup configurado" "PASS"
else
    test_result "Trap para cleanup configurado" "FAIL"
fi

if grep -q "cleanup_on_exit()" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Función cleanup_on_exit presente" "PASS"
else
    test_result "Función cleanup_on_exit presente" "FAIL"
fi

# Test 7: Verificar colores ANSI
print_header "Test 6: UI y colores"

COLOR_VARS=(
    "COLOR_RESET"
    "COLOR_RED"
    "COLOR_GREEN"
    "COLOR_YELLOW"
    "COLOR_CYAN"
)

for color in "${COLOR_VARS[@]}"; do
    if grep -q "${color}=" "${SCRIPT_DIR}/install-secure.sh"; then
        test_result "Color ${color} definido" "PASS"
    else
        test_result "Color ${color} definido" "FAIL"
    fi
done

# Test 8: Verificar logging
print_header "Test 7: Sistema de logs"

if grep -q "LOG_FILE=" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Variable LOG_FILE definida" "PASS"
else
    test_result "Variable LOG_FILE definida" "FAIL"
fi

if grep -q "log()" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Función log() presente" "PASS"
else
    test_result "Función log() presente" "FAIL"
fi

# Test 9: Verificar backup
print_header "Test 8: Sistema de backup"

if grep -q "BACKUP_DIR=" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Variable BACKUP_DIR definida" "PASS"
else
    test_result "Variable BACKUP_DIR definida" "FAIL"
fi

# Test 10: Verificar compatibilidad multiplataforma
print_header "Test 9: Compatibilidad multiplataforma"

if grep -q "OSTYPE" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Detección de OSTYPE" "PASS"
else
    test_result "Detección de OSTYPE" "FAIL"
fi

if grep -q "linux-gnu" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Soporte para Linux" "PASS"
else
    test_result "Soporte para Linux" "FAIL"
fi

if grep -q "darwin" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Soporte para macOS" "PASS"
else
    test_result "Soporte para macOS" "FAIL"
fi

if grep -q "microsoft.*proc.*version" "${SCRIPT_DIR}/install-secure.sh"; then
    test_result "Detección de WSL2" "PASS"
else
    test_result "Detección de WSL2" "FAIL"
fi

# Test 11: Verificar documentación
print_header "Test 10: Documentación"

if [[ -f "${SCRIPT_DIR}/INSTALL_SECURE_GUIDE.md" ]]; then
    test_result "Guía INSTALL_SECURE_GUIDE.md existe" "PASS"
else
    test_result "Guía INSTALL_SECURE_GUIDE.md existe" "FAIL"
fi

# Test 12: Verificar dependencias del sistema
print_header "Test 11: Verificación de dependencias del sistema"

# Docker
if command -v docker &>/dev/null; then
    docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    test_result "Docker instalado (v${docker_version})" "PASS"
else
    test_result "Docker instalado" "FAIL"
fi

# Docker Compose
if docker compose version &>/dev/null; then
    compose_version=$(docker compose version | grep -oP '\d+\.\d+' | head -1)
    test_result "Docker Compose V2 (v${compose_version})" "PASS"
elif command -v docker-compose &>/dev/null; then
    compose_version=$(docker-compose --version | grep -oP '\d+\.\d+' | head -1)
    test_result "Docker Compose V1 (v${compose_version} - legacy)" "PASS"
else
    test_result "Docker Compose instalado" "FAIL"
fi

# Python
if command -v python3 &>/dev/null; then
    python_version=$(python3 --version | grep -oP '\d+\.\d+')
    test_result "Python 3 instalado (v${python_version})" "PASS"
else
    test_result "Python 3 instalado" "FAIL"
fi

# Cryptography
if python3 -c "import cryptography" 2>/dev/null; then
    crypto_version=$(python3 -c "import cryptography; print(cryptography.__version__)" 2>/dev/null)
    test_result "Librería cryptography (v${crypto_version})" "PASS"
else
    test_result "Librería cryptography instalada" "FAIL"
fi

# Test 13: Verificar archivos necesarios
print_header "Test 12: Archivos necesarios"

REQUIRED_FILES=(
    "docker-compose-v2.2.0.yml"
    "validate_license.py"
    "security/rhinometric_public.pem"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${SCRIPT_DIR}/${file}" ]]; then
        test_result "Archivo ${file} existe" "PASS"
    else
        test_result "Archivo ${file} existe" "FAIL"
    fi
done

# Test 14: Verificar licencia (opcional)
print_header "Test 13: Licencia (opcional)"

if [[ -f "${SCRIPT_DIR}/licenses/cliente.lic" ]]; then
    test_result "Licencia cliente.lic presente" "PASS"
    
    # Intentar validar
    if python3 "${SCRIPT_DIR}/validate_license.py" &>/dev/null; then
        test_result "Licencia válida" "PASS"
    else
        test_result "Licencia válida" "FAIL"
    fi
else
    echo -e "${COLOR_YELLOW}⚠${COLOR_RESET} Licencia no encontrada (opcional para testing)"
fi

# Resumen final
print_header "RESUMEN DE TESTS"

total_tests=${#TEST_RESULTS[@]}
passed_tests=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^PASS:" || echo 0)
failed_tests=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^FAIL:" || echo 0)

echo "Total de tests: ${total_tests}"
echo -e "Tests pasados: ${COLOR_GREEN}${passed_tests}${COLOR_RESET}"
echo -e "Tests fallidos: ${COLOR_RED}${failed_tests}${COLOR_RESET}"
echo ""

if [[ $failed_tests -eq 0 ]]; then
    echo -e "${COLOR_GREEN}✓ TODOS LOS TESTS PASARON${COLOR_RESET}"
    echo ""
    echo "El instalador install-secure.sh está listo para uso."
    exit 0
else
    echo -e "${COLOR_RED}✗ ALGUNOS TESTS FALLARON${COLOR_RESET}"
    echo ""
    echo "Por favor revise los errores arriba."
    exit 1
fi
