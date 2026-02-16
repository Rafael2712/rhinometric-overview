#!/usr/bin/env python3
"""
Script de prueba end-to-end para sistema de emails enterprise.
Genera licencias demo+trial y envía email bundle.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.email_enterprise import send_trial_bundle_email

async def test_email_system():
    """
    Prueba completa del sistema de emails.
    Genera licencias de prueba y envía email bundle.
    """
    
    print("\n" + "="*80)
    print("🧪 TEST END-TO-END - SISTEMA DE EMAILS ENTERPRISE")
    print("="*80 + "\n")
    
    # Configuración SMTP Zoho
    smtp_config = {
        "host": "smtp.zoho.eu",
        "port": 465,
        "user": "rafael.canelon@rhinometric.com",
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_addr": "rafael.canelon@rhinometric.com"
    }
    
    if not smtp_config["password"]:
        print("❌ ERROR: SMTP_PASSWORD no configurado en variables de entorno")
        print("   Ejecuta: export SMTP_PASSWORD='tu_password_zoho'")
        return False
    
    # Datos de prueba
    test_customer_email = "rafael.canelon@rhinometric.com"
    test_customer_name = "Rafael Canelón (TEST)"
    test_demo_license = "RHINO-DEMO-2025-TEST1234ABCD"
    test_trial_license = "RHINO-TRIAL-2025-TEST5678EFGH"
    
    print(f"📧 Destinatario: {test_customer_email}")
    print(f"👤 Nombre: {test_customer_name}")
    print(f"🎯 Demo License: {test_demo_license}")
    print(f"🔬 Trial License: {test_trial_license}")
    print(f"📡 SMTP: {smtp_config['host']}:{smtp_config['port']}")
    print(f"👤 SMTP User: {smtp_config['user']}\n")
    
    # Enviar email
    print("📤 Enviando email bundle...\n")
    
    success = await send_trial_bundle_email(
        customer_email=test_customer_email,
        customer_name=test_customer_name,
        demo_license_key=test_demo_license,
        trial_license_key=test_trial_license,
        smtp_config=smtp_config,
        locale="es"
    )
    
    print("\n" + "="*80)
    if success:
        print("✅ TEST EXITOSO - Email enviado correctamente")
        print("="*80)
        print("\n📬 Verifica tu buzón de correo:")
        print(f"   - {test_customer_email}")
        print("   - Busca asunto: '🎯 Rhinometric Trial - Sus Licencias de Evaluación'")
        print("   - Verifica que contiene:")
        print("     ✓ Licencia Demo Cloud (4h)")
        print("     ✓ Licencia Trial (14d)")
        print("     ✓ Enlaces de descarga")
        print("     ✓ Documentación")
        print("     ✓ Información de soporte")
        print("     ✓ HTML renderizado correctamente\n")
    else:
        print("❌ TEST FALLIDO - Error al enviar email")
        print("="*80)
        print("\n🔍 Revisa los logs arriba para ver el error específico\n")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(test_email_system())
    sys.exit(0 if success else 1)
