#!/bin/bash
# ============================================
# Rhinometric v2.5.0 - Backup Script
# ============================================
# Backs up all persistent volumes and configs
# Usage: bash backup.sh
# Cron: 0 2 * * * /path/to/backup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Config
BACKUP_DIR="${BACKUP_DIR:-/var/backups/rhinometric}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="rhinometric_backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
LOG_FILE="$BACKUP_DIR/backup.log"

# Volumes to backup
VOLUMES=(
    "prometheus_data"
    "alertmanager_data"
    "grafana_data"
    "loki_data"
    "tempo_data"
    "postgres_data"
    "redis_data"
    "ai_models"
    "reports_output"
    "dashboard_builder_data"
)

# Config files
CONFIGS=(
    "docker-compose-prod.yml"
    ".env.prod"
    "traefik/traefik.yml"
    "prometheus/prometheus.yml"
    "prometheus/alerts/rhinometric.yml"
    "alertmanager/alertmanager.yml"
    "grafana/provisioning"
)

# Functions
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    log "${GREEN}✓ $1${NC}"
}

log_error() {
    log "${RED}✗ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠ $1${NC}"
}

# ============================================
# MAIN BACKUP
# ============================================

log "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log "${YELLOW}  RHINOMETRIC BACKUP - $DATE${NC}"
log "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create backup directory
mkdir -p "$BACKUP_PATH"/{volumes,configs}
log "Created backup directory: $BACKUP_PATH"

# Backup Docker volumes
log "\n${YELLOW}Backing up Docker volumes...${NC}"
for volume in "${VOLUMES[@]}"; do
    log "Backing up volume: $volume"
    
    if docker volume inspect "$volume" &>/dev/null; then
        # Create tar from volume
        docker run --rm \
            -v "$volume":/data:ro \
            -v "$BACKUP_PATH/volumes":/backup \
            alpine tar czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null
        
        if [ $? -eq 0 ]; then
            size=$(du -h "$BACKUP_PATH/volumes/${volume}.tar.gz" | cut -f1)
            log_success "$volume ($size)"
        else
            log_error "Failed to backup $volume"
        fi
    else
        log_warning "Volume $volume not found, skipping"
    fi
done

# Backup configs
log "\n${YELLOW}Backing up configuration files...${NC}"
for config in "${CONFIGS[@]}"; do
    if [ -e "$config" ]; then
        # Create directory structure
        mkdir -p "$BACKUP_PATH/configs/$(dirname "$config")"
        
        # Copy file or directory
        if [ -d "$config" ]; then
            cp -r "$config" "$BACKUP_PATH/configs/$(dirname "$config")/"
            log_success "$config (directory)"
        else
            cp "$config" "$BACKUP_PATH/configs/$config"
            log_success "$config"
        fi
    else
        log_warning "Config $config not found, skipping"
    fi
done

# Create metadata
log "\n${YELLOW}Creating backup metadata...${NC}"
cat > "$BACKUP_PATH/metadata.json" <<EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$DATE",
  "rhinometric_version": "2.5.0",
  "volumes_backed_up": $(printf '%s\n' "${VOLUMES[@]}" | jq -R . | jq -s .),
  "configs_backed_up": $(printf '%s\n' "${CONFIGS[@]}" | jq -R . | jq -s .),
  "hostname": "$(hostname)",
  "backup_size": "$(du -sh "$BACKUP_PATH" | cut -f1)"
}
EOF
log_success "Metadata created"

# Create final archive
log "\n${YELLOW}Creating final archive...${NC}"
cd "$BACKUP_DIR"
tar czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME" 2>/dev/null

if [ $? -eq 0 ]; then
    # Verify archive
    tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        final_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        log_success "Archive created and verified (${final_size})"
        
        # Remove temp directory
        rm -rf "$BACKUP_PATH"
        log "Removed temporary directory"
        
        # Calculate checksum
        checksum=$(sha256sum "${BACKUP_NAME}.tar.gz" | cut -d' ' -f1)
        echo "$checksum" > "${BACKUP_NAME}.tar.gz.sha256"
        log_success "Checksum: $checksum"
    else
        log_error "Archive verification failed"
        exit 1
    fi
else
    log_error "Failed to create archive"
    exit 1
fi

# Rotate old backups
log "\n${YELLOW}Rotating old backups (keeping last $RETENTION_DAYS days)...${NC}"
find "$BACKUP_DIR" -name "rhinometric_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null
find "$BACKUP_DIR" -name "rhinometric_backup_*.tar.gz.sha256" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null

deleted=$(find "$BACKUP_DIR" -name "rhinometric_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS | wc -l)
if [ $deleted -gt 0 ]; then
    log_success "Deleted $deleted old backup(s)"
else
    log "No old backups to delete"
fi

# Summary
log "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log "${GREEN}  BACKUP COMPLETED SUCCESSFULLY${NC}"
log "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log "Backup file: ${BACKUP_NAME}.tar.gz"
log "Size: $(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)"
log "Location: $BACKUP_DIR"
log ""

# List all backups
log "Available backups:"
ls -lh "$BACKUP_DIR"/rhinometric_backup_*.tar.gz 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

exit 0
