#!/bin/bash
# first-boot.sh - OVA First Boot Initialization
# Rhinometric Demo Appliance v2.5.0
# Ejecutado UNA VEZ por systemd al primer arranque

set -euo pipefail

LOCK_FILE="/var/lib/rhinometric/first-boot.lock"
RHINO_HOME="/opt/rhinometric"
LOG_FILE="/var/log/rhinometric/first-boot.log"

mkdir -p "$(dirname "$LOCK_FILE")" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Prevenir ejecuciÃ³n mÃºltiple
if [ -f "$LOCK_FILE" ]; then
    log "âš ï¸  First boot ya ejecutado previamente (lock existe)"
    exit 0
fi

log "========================================="
log "íº€ RHINOMETRIC DEMO APPLIANCE v2.5.0"
log "   First Boot Initialization"
log "========================================="

# 1. Verificar Docker instalado
if ! command -v docker &> /dev/null; then
    log "âŒ Docker no encontrado - instalando..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    systemctl enable docker
    systemctl start docker
    log "âœ“ Docker instalado"
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    log "âŒ Docker Compose no encontrado - instalando..."
    curl -SL "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log "âœ“ Docker Compose instalado"
fi

# 2. Configurar usuario rhinouser
if ! id "rhinouser" &>/dev/null; then
    useradd -m -s /bin/bash rhinouser
    echo "rhinouser:rhinometric" | chpasswd
    usermod -aG sudo,docker rhinouser
    log "âœ“ Usuario rhinouser creado"
fi

# 3. Generar certificados TLS self-signed si no existen
CERT_DIR="$RHINO_HOME/deploy/demo/traefik/certs"
if [ ! -f "$CERT_DIR/cert.pem" ]; then
    log "í´ Generando certificados TLS self-signed..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" \
        -days 365 \
        -subj "/C=US/ST=Demo/L=Demo/O=Rhinometric/CN=rhinometric-demo.local" \
        2>&1 | tee -a "$LOG_FILE"
    log "âœ“ Certificados generados"
fi

# 4. Levantar stack Docker Compose
log "í°³ Iniciando stack Rhinometric..."
cd "$RHINO_HOME/deploy/demo"

if [ -f "docker-compose-demo.yml" ]; then
    docker compose -f docker-compose-demo.yml up -d 2>&1 | tee -a "$LOG_FILE"
else
    log "âŒ docker-compose-demo.yml no encontrado en $PWD"
    exit 1
fi

# 5. Esperar healthchecks (max 5 min)
log "â³ Esperando healthchecks de servicios..."
TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    HEALTHY=$(docker ps --filter "name=rhinometric-" --filter "health=healthy" --format "{{.Names}}" | wc -l)
    TOTAL=$(docker ps --filter "name=rhinometric-" --format "{{.Names}}" | wc -l)
    
    log "  Healthy: $HEALTHY / $TOTAL"
    
    if [ "$HEALTHY" -ge 10 ]; then
        log "âœ… Servicios listos ($HEALTHY/$TOTAL healthy)"
        break
    fi
    
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    log "âš ï¸  Timeout esperando healthchecks - continuando anyway"
fi

# 6. Ejecutar smoke test
log "í·ª Ejecutando smoke test..."
if bash "$RHINO_HOME/deploy/demo/scripts/smoke-test.sh" 2>&1 | tee -a "$LOG_FILE"; then
    log "âœ… Smoke test PASSED"
else
    log "âš ï¸  Smoke test FAILED - revisar logs"
fi

# 7. Iniciar anomaly-seed en background
log "í¼± Iniciando anomaly-seed.sh..."
nohup bash "$RHINO_HOME/deploy/demo/scripts/anomaly-seed.sh" > /var/log/rhinometric/anomaly-seed.log 2>&1 &
SEED_PID=$!
log "âœ“ Anomaly seed iniciado (PID: $SEED_PID)"

# 8. Obtener IP de la VM
VM_IP=$(hostname -I | awk '{print $1}')

# 9. Mostrar banner de Ã©xito
log ""
log "========================================="
log "âœ… RHINOMETRIC DEMO READY"
log "========================================="
log ""
log "Acceso:"
log "  Grafana:           https://$VM_IP:3000"
log "  Dashboard Builder: http://$VM_IP:3001"
log "  Prometheus:        http://$VM_IP:9090"
log "  Credentials:       admin / rhinometric_demo"
log ""
log "SSH:"
log "  ssh rhinouser@$VM_IP"
log "  Password: rhinometric"
log ""
log "Logs:"
log "  First boot:   $LOG_FILE"
log "  Anomaly seed: /var/log/rhinometric/anomaly-seed.log"
log ""
log "Smoke test:"
log "  cd /opt/rhinometric/deploy/demo"
log "  bash scripts/smoke-test.sh"
log ""
log "========================================="

# 10. Crear lock file
touch "$LOCK_FILE"
log "âœ“ First boot completado - lock creado"

exit 0
