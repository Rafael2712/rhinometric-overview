#!/bin/bash
# Monitor de licencias activas
LICENSES_DIR="/mnt/c/Users/canel/mi-proyecto/licenses_issued"
mkdir -p $LICENSES_DIR

# Registrar nueva licencia
register_license() {
    echo "$(date)|$1|$2|$3" >> $LICENSES_DIR/active.log
}

# Ver licencias activas
show_licenses() {
    echo "=== LICENCIAS ACTIVAS ==="
    while IFS='|' read -r date customer type expires; do
        echo "Cliente: $customer | Tipo: $type | Expira: $expires"
    done < $LICENSES_DIR/active.log
}

# Contar licencias
count_licenses() {
    total=$(wc -l < $LICENSES_DIR/active.log)
    trial=$(grep -c "trial" $LICENSES_DIR/active.log)
    paid=$(grep -c "paid" $LICENSES_DIR/active.log)
    echo "Total: $total | Trial: $trial | Pagadas: $paid"
}

case "$1" in
    register) register_license "$2" "$3" "$4";;
    show) show_licenses;;
    count) count_licenses;;
    *) echo "Uso: $0 {register|show|count}";;
esac
