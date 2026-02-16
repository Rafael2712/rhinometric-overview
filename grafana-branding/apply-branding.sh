#!/bin/bash

# Rhinometric Branding Application Script
# This script applies Rhinometric branding to Grafana

echo "🎨 Applying Rhinometric Branding to Grafana..."

# Copy custom logo
cp /branding/img/rhinometric_logo.svg /usr/share/grafana/public/img/grafana_icon.svg
cp /branding/img/rhinometric_logo.svg /usr/share/grafana/public/img/grafana_com_auth_icon.svg
cp /branding/img/rhinometric_logo.svg /usr/share/grafana/public/img/grafana_net_logo.svg
cp /branding/img/rhinometric_logo.svg /usr/share/grafana/public/img/grafana_mask_icon.svg

# Copy favicon
cp /branding/img/rhinometric_icon.svg /usr/share/grafana/public/img/fav32.png
cp /branding/img/rhinometric_icon.svg /usr/share/grafana/public/img/fav16.png
cp /branding/img/rhinometric_icon.svg /usr/share/grafana/public/img/apple-touch-icon.png

# Modify index.html title
sed -i 's/<title>Grafana<\/title>/<title>Rhinometric Observability Platform<\/title>/g' /usr/share/grafana/public/views/index.html

# Add custom CSS for branding
cat >> /usr/share/grafana/public/build/custom.css << 'EOF'
/* Rhinometric Custom Branding */
.sidemenu__logo {
  background: linear-gradient(90deg, #00d4aa 0%, #00ffcc 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  font-weight: 700 !important;
}

.login-branding {
  color: #00d4aa !important;
}

.footer a {
  color: #00d4aa !important;
}

.page-header__title::before {
  content: "RHINOMETRIC - ";
  color: #00d4aa;
  font-weight: 700;
}
EOF

echo "✅ Rhinometric branding applied successfully!"
