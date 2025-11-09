# ��� Rhinometric v2.5.0 - Branding Implementation Summary

**Version**: 2.5.0  
**Date**: November 9, 2024  
**Status**: Complete Multi-Layer Branding

---

## ��� Overview

Rhinometric v2.5.0 implements comprehensive enterprise branding across all customer touchpoints:

1. Landing Page (Nginx/Traefik)
2. Grafana UI (custom theme + plugin)
3. Email Templates (Alertmanager)
4. System MOTD (SSH/console)
5. HTTP Headers (X-Powered-By)

**License Tiers**:
- **Starter**: Logo only
- **Professional**: Logo + colors
- **Enterprise**: Full white-label (unlimited customization)

---

## ��� 1. Landing Page Branding

**File**: `infrastructure/mi-proyecto/nginx/html/index.html`

**Customizable Elements**:
- Company logo (`<img src="logo.png">`)
- Company name (h1, title)
- Tagline/description
- Color scheme (CSS variables)
- Hero image
- Contact information
- Feature highlights

**Implementation**:
```html
<div class="hero">
  <img src="/assets/rhinometric-logo.svg" alt="Rhinometric">
  <h1>Rhinometric Enterprise</h1>
  <p>Plataforma de Observabilidad Empresarial</p>
</div>
```

**CSS Variables**:
```css
:root {
  --brand-primary: #1E3A8A;    /* Blue */
  --brand-secondary: #10B981;  /* Green */
  --brand-accent: #F59E0B;     /* Orange */
}
```

---

## ���️ 2. Grafana Theme Customization

**Method**: Custom plugin `rhinometric-dashboard-builder`

**Customizable Elements**:
- Sidebar logo
- Login page logo
- Theme colors (dark/light mode)
- Custom fonts
- Footer text

**Implementation**:
```typescript
// grafana-plugins/rhinometric-dashboard-builder/theme.ts
export const brandedTheme = {
  colors: {
    primary: '#1E3A8A',
    secondary: '#10B981',
    accent: '#F59E0B'
  },
  logo: {
    sidebar: '/public/plugins/rhinometric-dashboard-builder/img/logo.svg',
    login: '/public/plugins/rhinometric-dashboard-builder/img/logo-full.svg'
  }
};
```

**Configuration** (`grafana.ini`):
```ini
[branding]
app_title = Rhinometric Enterprise
logo = /public/plugins/rhinometric-dashboard-builder/img/logo.svg
```

---

## ��� 3. Email Template Branding

**Files**: `deploy/*/alertmanager/templates/email.html`

**Customizable Elements**:
- Company logo (header)
- Colors (header, footer, buttons)
- Company name
- Contact email
- Footer disclaimer

**Template**:
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .header { background-color: #1E3A8A; color: white; }
    .logo { max-width: 200px; }
    .button { background-color: #10B981; }
  </style>
</head>
<body>
  <div class="header">
    <img src="https://rhinometric.com/logo.png" class="logo">
    <h1>Rhinometric Enterprise Alert</h1>
  </div>
  <div class="content">
    {{ range .Alerts }}
    <h2>{{ .Labels.alertname }}</h2>
    <p>{{ .Annotations.description }}</p>
    {{ end }}
  </div>
  <div class="footer">
    <p>Rhinometric Enterprise Monitoring Platform</p>
    <p>Contact: rafael.canelon@rhinometric.com</p>
  </div>
</body>
</html>
```

**Alertmanager Config**:
```yaml
templates:
  - '/etc/alertmanager/templates/*.html'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'team@company.com'
        from: 'rafael.canelon@rhinometric.com'
        headers:
          From: 'Rhinometric Alerts <rafael.canelon@rhinometric.com>'
          Subject: '{{ template "email.subject" . }}'
        html: '{{ template "email.html" . }}'
```

---

## ��� 4. MOTD Branding

**File**: `packer/99-rhinometric-motd`

**Implementation**:
```bash
#!/bin/bash
cat << 'MOTD'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ██████╗ ██╗  ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗   ║
║        ██╔══██╗██║  ██║██║████╗  ██║██╔═══██╗████╗ ████║   ║
║        ██████╔╝███████║██║██╔██╗ ██║██║   ██║██╔████╔██║   ║
║        ██╔══██╗██╔══██║██║██║╚██╗██║██║   ██║██║╚██╔╝██║   ║
║        ██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║   ║
║        ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝   ║
║                                                              ║
║             Enterprise Observability Platform                ║
║                        Version 2.5.0                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

��� Grafana Dashboard: https://localhost/grafana (admin/rhinometric_v22)
��� Prometheus: https://localhost/prometheus
��� Alertmanager: https://localhost/alertmanager

��� Support: rafael.canelon@rhinometric.com
��� Docs: https://docs.rhinometric.com

��� Services Status:
MOTD

docker ps --format "   {{.Names}}: {{.Status}}" | grep rhinometric

cat << 'FOOTER'

��� Quick Commands:
   docker-compose logs -f          # View all logs
   docker-compose restart grafana  # Restart Grafana
   docker ps                       # Check services
FOOTER
```

**Installation** (OVA):
```bash
cp 99-rhinometric-motd /etc/update-motd.d/
chmod +x /etc/update-motd.d/99-rhinometric-motd
```

---

## ��� 5. HTTP Headers Branding

**Traefik** (`traefik.yml`):
```yaml
http:
  middlewares:
    branded-headers:
      headers:
        customResponseHeaders:
          X-Powered-By: "Rhinometric Enterprise v2.5.0"
          Server: "Rhinometric"
```

**Nginx** (`nginx.conf`):
```nginx
add_header X-Powered-By "Rhinometric Enterprise v2.5.0";
add_header Server "Rhinometric";
```

---

## ��� Branding Assets Structure

```
packer/branding/
├── logos/
│   ├── logo.svg            # Main logo (color)
│   ├── logo-white.svg      # White version
│   ├── logo-icon.svg       # Icon only
│   └── logo-full.svg       # Logo + text
├── images/
│   ├── hero.jpg            # Landing page hero
│   └── favicon.ico         # Browser icon
├── fonts/
│   └── custom-font.woff2   # Optional custom font
└── colors/
    └── palette.json        # Color definitions
```

---

## ��� Customization Process

### For Professional Edition

1. **Prepare Assets**:
   - Logo: SVG format, transparent background
   - Colors: Primary, secondary, accent (hex codes)
   - Company name

2. **Update Landing Page**:
   ```bash
   cd infrastructure/mi-proyecto/nginx/html
   # Replace logo
   cp /path/to/client-logo.svg assets/logo.svg
   # Update index.html with client colors
   sed -i 's/#1E3A8A/#CLIENT_COLOR/g' index.html
   ```

3. **Update Grafana**:
   ```bash
   cd grafana-plugins/rhinometric-dashboard-builder
   cp /path/to/logo.svg img/logo.svg
   # Update theme.ts with client colors
   ```

4. **Update Email Templates**:
   ```bash
   cd deploy/prod/alertmanager/templates
   # Update email.html with client logo URL
   sed -i 's|https://rhinometric.com/logo.png|https://client.com/logo.png|' email.html
   ```

5. **Rebuild & Deploy**:
   ```bash
   docker-compose down
   docker-compose build --no-cache grafana nginx
   docker-compose up -d
   ```

### For Enterprise Edition (White-Label)

**Additional Customizations**:
- Remove "Rhinometric" references entirely
- Custom domain (monitoring.client.com)
- Custom SSL certificates
- Custom MOTD
- Custom documentation URLs

**Script**: `scripts/apply-branding.sh`
```bash
#!/bin/bash
CLIENT_NAME="$1"
CLIENT_LOGO="$2"
PRIMARY_COLOR="$3"

# Automated replacement across all files
find . -name "*.html" -o -name "*.ts" -o -name "*.yml" | \
  xargs sed -i "s/Rhinometric/${CLIENT_NAME}/g"

# Apply colors
find . -name "*.css" | \
  xargs sed -i "s/#1E3A8A/${PRIMARY_COLOR}/g"
```

---

## ✅ Verification Checklist

- [ ] Landing page shows custom logo and colors
- [ ] Grafana sidebar shows custom logo
- [ ] Grafana login page shows custom logo
- [ ] Email alerts have branded template
- [ ] MOTD displays on SSH login
- [ ] HTTP headers show custom X-Powered-By
- [ ] Favicon matches brand
- [ ] All "Rhinometric" references updated (Enterprise only)

---

## ��� Implementation Matrix

| Element | Starter | Professional | Enterprise |
|---------|---------|--------------|------------|
| Logo (Landing) | ✅ | ✅ | ✅ |
| Logo (Grafana) | ❌ | ✅ | ✅ |
| Colors (Landing) | ❌ | ✅ | ✅ |
| Colors (Grafana) | ❌ | ✅ | ✅ |
| Email Templates | ❌ | ✅ | ✅ |
| MOTD | ❌ | ❌ | ✅ |
| HTTP Headers | ❌ | ❌ | ✅ |
| Remove "Rhinometric" | ❌ | ❌ | ✅ |
| Custom Domain | ❌ | ❌ | ✅ |
| Custom Docs URL | ❌ | ❌ | ✅ |

---

## ��� Contact

**Branding Support**: rafael.canelon@rhinometric.com  
**Docs**: https://docs.rhinometric.com/branding  
**Assets**: https://rhinometric.com/branding-kit

---

**Status**: ✅ Full branding implementation complete  
**Last Updated**: November 9, 2024
