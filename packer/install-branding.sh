#!/bin/bash
set -e

echo "=== RHINOMETRIC BRANDING INSTALLATION ==="

# 1. Instalar MOTD
echo "→ Installing MOTD banner..."
sudo cp /tmp/packer-files/packer/99-rhinometric-motd /etc/update-motd.d/99-rhinometric
sudo chmod +x /etc/update-motd.d/99-rhinometric
sudo chown root:root /etc/update-motd.d/99-rhinometric

# 2. Deshabilitar MOTDs por defecto de Ubuntu
echo "→ Disabling default Ubuntu MOTD scripts..."
sudo chmod -x /etc/update-motd.d/10-help-text 2>/dev/null || true
sudo chmod -x /etc/update-motd.d/50-motd-news 2>/dev/null || true
sudo chmod -x /etc/update-motd.d/88-esm-announce 2>/dev/null || true

# 3. Copiar branding files a /opt/rhinometric
echo "→ Copying branding assets..."
sudo mkdir -p /opt/rhinometric/branding
sudo cp -r /tmp/packer-files/deploy/demo/branding/* /opt/rhinometric/branding/
sudo chown -R rhinouser:rhinouser /opt/rhinometric/branding

# 4. Crear placeholder logo si no existe
if [ ! -f /opt/rhinometric/branding/logos/rhinometric-logo.svg ]; then
    echo "→ Creating placeholder logo..."
    sudo mkdir -p /opt/rhinometric/branding/logos
    cat <<'EOSVG' | sudo tee /opt/rhinometric/branding/logos/rhinometric-logo.svg > /dev/null
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 50">
  <defs>
    <linearGradient id="rhino-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e5a7d;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2d8ab8;stop-opacity:1" />
    </linearGradient>
  </defs>
  <text x="10" y="35" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="url(#rhino-gradient)">
    RHINOMETRIC
  </text>
</svg>
EOSVG
    sudo chown rhinouser:rhinouser /opt/rhinometric/branding/logos/rhinometric-logo.svg
fi

# 5. Configurar permisos finales
sudo chmod -R 755 /opt/rhinometric/branding

echo "✅ Branding installation complete"
echo "   - MOTD: /etc/update-motd.d/99-rhinometric"
echo "   - Assets: /opt/rhinometric/branding/"
echo "   - Logo: /opt/rhinometric/branding/logos/rhinometric-logo.svg"

