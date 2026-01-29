#!/bin/bash
set -e

echo "=== Deploying Alertmanager Notifications (Slack + Email) ==="

# Check if .env.alertmanager exists
if [ ! -f ".env.alertmanager" ]; then
  echo "❌ ERROR: .env.alertmanager not found"
  echo ""
  echo "Please create it from template:"
  echo "  cp .env.alertmanager.template .env.alertmanager"
  echo "  nano .env.alertmanager  # Edit with your credentials"
  echo ""
  exit 1
fi

# Load environment variables
source .env.alertmanager

# Validate required variables
if [[ "$SLACK_WEBHOOK_URL" == *"YOUR/WEBHOOK/URL"* ]]; then
  echo "⚠️  WARNING: SLACK_WEBHOOK_URL not configured properly"
  echo "Get your webhook URL from: https://api.slack.com/apps"
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

if [[ "$SMTP_PASSWORD" == "your_zoho_password_here" ]]; then
  echo "⚠️  WARNING: SMTP_PASSWORD not configured"
  read -p "Continue without email notifications? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Expand variables in config template
echo "Expanding environment variables in config..."
envsubst < config/alertmanager-notifications.yml > /tmp/alertmanager.yml.expanded

# Backup current config
if [ ! -d "alertmanager" ]; then
  mkdir -p alertmanager/templates
fi

if [ -f "alertmanager/alertmanager.yml" ]; then
  cp alertmanager/alertmanager.yml alertmanager/alertmanager.yml.backup-$(date +%Y%m%d-%H%M%S)
  echo "✓ Backup created"
fi

# Copy expanded config
cp /tmp/alertmanager.yml.expanded alertmanager/alertmanager.yml
echo "✓ Configuration updated"

# Validate config
echo "Validating Alertmanager config..."
docker run --rm -v $(pwd)/alertmanager:/etc/alertmanager prom/alertmanager:v0.27.0 \
  amtool check-config /etc/alertmanager/alertmanager.yml

if [ $? -eq 0 ]; then
  echo "✓ Configuration valid"
else
  echo "❌ Configuration invalid - restoring backup"
  cp alertmanager/alertmanager.yml.backup-* alertmanager/alertmanager.yml
  exit 1
fi

# Restart alertmanager
echo "Restarting Alertmanager..."
docker restart rhinometric-alertmanager

sleep 5

# Check status
if docker ps | grep -q rhinometric-alertmanager; then
  echo "✓ Alertmanager running"
else
  echo "❌ Alertmanager failed to start"
  docker logs rhinometric-alertmanager --tail 20
  exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Notifications configured:"
echo "  🔥 Critical alerts → Slack + Email"
echo "  ⚠️  Warning alerts → Slack only"
echo "  ℹ️  Info alerts → Email only"
echo ""
echo "Test by triggering an alert or visit:"
echo "  http://89.167.15.73:9093"
echo ""
