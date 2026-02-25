#!/usr/bin/env bash
set -euo pipefail
echo "RHINOMETRIC FULL WIPE"
echo "This will DESTROY ALL rhinometric data!"
read -rp "Type WIPE to confirm: " confirm
if [[ "$confirm" != "WIPE" ]]; then echo "Cancelled."; exit 0; fi
echo "[1/6] Stopping containers..."
cd /opt/rhinometric 2>/dev/null
docker compose -f docker-compose-trial.yml --env-file .env down -v --remove-orphans 2>/dev/null || true
docker compose down -v --remove-orphans 2>/dev/null || true
echo "[2/6] Removing containers..."
docker ps -a --filter "name=rhinometric" -q 2>/dev/null | xargs -r docker rm -f 2>/dev/null || true
echo "[3/6] Removing images..."
docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -iE "rhinometric|license|console|ai-anomaly" | xargs -r docker rmi -f 2>/dev/null || true
echo "[4/6] Removing volumes..."
docker volume ls -q 2>/dev/null | grep -i rhinometric | xargs -r docker volume rm -f 2>/dev/null || true
echo "[5/6] Removing data..."
rm -rf /root/rhinometric_data_v2.5 /home/*/rhinometric_data_v2.5 2>/dev/null || true
echo "[6/6] Cleaning generated files..."
rm -f /opt/rhinometric/.env /opt/rhinometric/CREDENTIALS.txt 2>/dev/null || true
rm -f /usr/local/bin/rhinoctl /var/log/rhinometric-install.log 2>/dev/null || true
echo ""
echo "WIPE COMPLETE. To reinstall: cd /opt/rhinometric; sudo bash trial-package/install.sh"
