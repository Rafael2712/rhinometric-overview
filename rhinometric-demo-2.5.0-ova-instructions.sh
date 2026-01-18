#!/bin/bash
# Rhinometric Demo OVA - Quick Start Guide v2.5.0
# Evaluación rápida de 4 horas
# Autor: Rafael Canelón
# Fecha: 16 Diciembre 2025

set -e

VERSION="2.5.0"
DEMO_HOURS=4

echo "=========================================="
echo "🦏 Rhinometric Demo OVA v${VERSION}"
echo "=========================================="
echo ""
echo "⚠️  DEMO DE EVALUACIÓN - ${DEMO_HOURS} HORAS"
echo ""
echo "Este archivo OVA contiene:"
echo "  • Stack completo pre-configurado"
echo "  • Grafana 11.x + Prometheus + Loki"
echo "  • Console v3 + AI Anomaly Engine"
echo "  • Datos de ejemplo pre-cargados"
echo ""

# === INSTRUCCIONES ===
cat << 'EOFINSTRUCTIONS'
📋 INSTRUCCIONES DE USO:

1️⃣  IMPORTAR EN VIRTUALBOX/VMWARE
   
   VirtualBox:
   -----------
   • File → Import Appliance
   • Seleccionar: rhinometric-demo-2.5.0.ova
   • Settings recomendados:
     - RAM: 8GB (mínimo 4GB)
     - CPU: 4 cores (mínimo 2)
     - Disk: 50GB
   • Start → Esperar 2-3 minutos

   VMware Workstation:
   ------------------
   • File → Open → rhinometric-demo-2.5.0.ova
   • Edit Settings:
     - Memory: 8GB
     - Processors: 4
   • Power On

2️⃣  ACCESO AL SISTEMA

   Una vez iniciada la VM, abrir navegador en:
   
   🌐 Grafana (Dashboard principal)
      http://localhost:3000
      Usuario: demo
      Contraseña: rhinometric2025

   📊 Console v3 (Gestión)
      http://localhost:3002
      Usuario: admin
      Contraseña: rhinometric2025

   📈 Prometheus (Métricas)
      http://localhost:9090

3️⃣  FUNCIONALIDADES DEMO

   ✅ Dashboards pre-configurados (15)
   ✅ Datos sintéticos en tiempo real
   ✅ Alertas de ejemplo
   ✅ AI Anomaly Detection
   ✅ Distributed Tracing
   ✅ Logs centralizados

4️⃣  LIMITACIONES DEMO

   ⚠️  Expira en: 4 horas desde primera ejecución
   ⚠️  Máximo 5 nodos monitorizados
   ⚠️  Retención de datos: 24 horas
   ⚠️  Sin soporte técnico

5️⃣  UPGRADE A PRODUCCIÓN

   Para continuar usando Rhinometric:
   
   📧 Contacto: rafael.canelon@rhinometric.com
   
   Opciones disponibles:
   • Trial 14 días (completo, sin limitaciones)
   • Annual License (1 año, producción)
   • Enterprise (contactar para cotización)

6️⃣  TROUBLESHOOTING

   VM no arranca:
   -------------
   • Verificar que Virtualization (VT-x/AMD-V) está habilitado en BIOS
   • Aumentar RAM asignada a 8GB
   • Verificar espacio en disco (50GB libres)

   No puedo acceder a localhost:3000:
   ---------------------------------
   • Verificar que la VM está corriendo
   • Esperar 2-3 minutos después de iniciar
   • Probar con: http://192.168.56.10:3000
   • En VMware, verificar configuración de red (NAT o Bridged)

   Pantalla negra en la VM:
   -----------------------
   • Presionar Enter
   • Login: rhinometric / Password: demo2025
   • Ejecutar: sudo systemctl status docker

========================================
📚 DOCUMENTACIÓN COMPLETA
========================================

Descargar guías en PDF:
• http://rhinometric.com/docs/installation-guide?lang=es
• http://rhinometric.com/docs/user-manual?lang=es

Videos tutoriales:
• YouTube: @RhinometricOfficial

========================================
🦏 ¡Disfruta evaluando Rhinometric!
========================================

EOFINSTRUCTIONS

echo ""
echo "⚠️  NOTA IMPORTANTE:"
echo ""
echo "Este archivo (rhinometric-demo-2.5.0-ova-instructions.sh)"
echo "NO es el OVA real, es la guía de instalación."
echo ""
echo "El archivo OVA real es un archivo binario de ~3GB que debe"
echo "generarse desde una VM configurada usando:"
echo ""
echo "  1. Configurar VM Ubuntu 22.04 con Docker"
echo "  2. Instalar Rhinometric completo"
echo "  3. Configurar licencia demo de 4 horas"
echo "  4. Exportar VM como OVA:"
echo "     VirtualBox → File → Export Appliance"
echo ""
echo "Para obtener el OVA real, contacte:"
echo "  📧 rafael.canelon@rhinometric.com"
echo ""
