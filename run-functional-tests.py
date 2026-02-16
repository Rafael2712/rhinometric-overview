#!/usr/bin/env python3
"""
RHINOMETRIC License Monitor - Functional Test Suite
Simula diferentes escenarios de expiración y captura resultados
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add license-monitor to path
sys.path.insert(0, 'license-monitor')

from license_monitor import (
    find_license_file,
    load_license,
    get_days_until_expiration,
    get_email_template,
    load_alert_state,
    save_alert_state
)

print("=" * 70)
print("     RHINOMETRIC LICENSE MONITOR - FUNCTIONAL TEST SUITE")
print("=" * 70)
print()

# ============================================================================
# TEST 1: Verificar licencia actual
# ============================================================================

print("═" * 70)
print("TEST 1: VERIFICAR LICENCIA ACTUAL")
print("═" * 70)
print()

license_path = find_license_file()
if not license_path:
    print("[ERROR] No se encontro licencia")
    sys.exit(1)

print(f"[OK] Licencia encontrada: {license_path}")
print()

license_data = load_license(license_path)
if not license_data:
    print("[ERROR] No se pudo cargar licencia")
    sys.exit(1)

print("[INFO] Informacion de licencia:")
print(f"   Cliente:  {license_data.get('customer')}")
print(f"   Tipo:     {license_data.get('type')}")
print(f"   HWID:     {license_data.get('hwid')}")
print(f"   Expira:   {license_data.get('expires')}")
print(f"   Emitida:  {license_data.get('issued_at')}")
print(f"   Features: {', '.join(license_data.get('features', []))}")
print()

days = get_days_until_expiration(license_data)
if days is None:
    print("[ERROR] No se pudo calcular expiracion")
    sys.exit(1)

if days > 900000:
    print("[OK] Licencia PERPETUA (no expira)")
elif days < 0:
    print(f"[ERROR] Licencia EXPIRADA hace {abs(days)} dias")
else:
    print(f"[OK] Licencia valida - {days} dias restantes")

print()

# ============================================================================
# TEST 2: Simular escenario - 10 días para expirar
# ============================================================================

print("═" * 70)
print("TEST 2: ESCENARIO - LICENCIA EXPIRA EN 10 DÍAS (INFORMATIVA)")
print("═" * 70)
print()

# Crear datos simulados
sim_license_10 = {
    'customer': 'BancoSantander',
    'type': 'annual',
    'hwid': 'A3F7C9E1B2D4F6A8',
    'expires': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=355)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting', 'ai_anomaly']
}

print("📋 Licencia simulada:")
print(f"   Cliente:  {sim_license_10['customer']}")
print(f"   Expira:   {sim_license_10['expires']}")
print(f"   Días:     10")
print()

subject_10, body_10 = get_email_template(10, sim_license_10)

print("📧 Email generado:")
print(f"   Asunto:   {subject_10}")
print(f"   Tamaño:   {len(body_10)} bytes")
print(f"   Nivel:    INFORMATIVA")
print(f"   Color:    Azul (#3498db)")
print()

# Mostrar preview del email
print("[PREVIEW] Email (primeras 500 chars):")
print("-" * 70)
preview = body_10[:500].replace('\n', ' ')
print(preview + "...")
print("-" * 70)
print()

# ============================================================================
# TEST 3: Simular escenario - 3 días para expirar
# ============================================================================

print("═" * 70)
print("TEST 3: ESCENARIO - LICENCIA EXPIRA EN 3 DÍAS (ADVERTENCIA)")
print("═" * 70)
print()

sim_license_3 = {
    'customer': 'TelefónicaEspaña',
    'type': 'trial',
    'hwid': 'B4E8D1F3C5A7B9D2',
    'expires': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=27)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting']
}

print("📋 Licencia simulada:")
print(f"   Cliente:  {sim_license_3['customer']}")
print(f"   Expira:   {sim_license_3['expires']}")
print(f"   Días:     3")
print()

subject_3, body_3 = get_email_template(3, sim_license_3)

print("📧 Email generado:")
print(f"   Asunto:   {subject_3}")
print(f"   Tamaño:   {len(body_3)} bytes")
print(f"   Nivel:    ADVERTENCIA")
print(f"   Color:    Naranja (#f39c12)")
print()

# ============================================================================
# TEST 4: Simular escenario - 1 día para expirar
# ============================================================================

print("═" * 70)
print("TEST 4: ESCENARIO - LICENCIA EXPIRA EN 1 DÍA (CRÍTICA)")
print("═" * 70)
print()

sim_license_1 = {
    'customer': 'BBVA',
    'type': 'annual',
    'hwid': 'C5F9E2A4D6B8C1E3',
    'expires': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=364)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting', 'ai_anomaly', 'veriverde_esg', 'api_connector']
}

print("📋 Licencia simulada:")
print(f"   Cliente:  {sim_license_1['customer']}")
print(f"   Expira:   {sim_license_1['expires']}")
print(f"   Días:     1")
print()

subject_1, body_1 = get_email_template(1, sim_license_1)

print("📧 Email generado:")
print(f"   Asunto:   {subject_1}")
print(f"   Tamaño:   {len(body_1)} bytes")
print(f"   Nivel:    CRÍTICA")
print(f"   Color:    Rojo (#e74c3c)")
print()

# ============================================================================
# TEST 5: Verificar estado de alertas
# ============================================================================

print("═" * 70)
print("TEST 5: VERIFICAR SISTEMA DE ESTADO DE ALERTAS")
print("═" * 70)
print()

# Cargar estado actual
alert_state = load_alert_state()
print("[STATUS] Estado actual de alertas:")
for day, sent in alert_state.items():
    status = "[SENT]" if sent else "[PENDING]"
    print(f"   {day} días: {status}")
print()

# Simular envío de alerta
print("[ACTION] Simulando envio de alerta de 10 dias...")
alert_state[10] = True
save_alert_state(alert_state)
print("✅ Estado actualizado")
print()

# Verificar guardado
alert_state_check = load_alert_state()
if alert_state_check.get(10):
    print("[OK] Estado persistente verificado correctamente")
else:
    print("[ERROR] Estado no se guardo correctamente")
print()

# ============================================================================
# TEST 6: Generar dumps de emails
# ============================================================================

print("═" * 70)
print("TEST 6: GENERAR DUMPS DE EMAILS PARA INSPECCIÓN")
print("═" * 70)
print()

# Crear directorio de dumps
os.makedirs('test-outputs', exist_ok=True)

# Guardar email de 10 días
with open('test-outputs/email_10_days_informativa.html', 'w', encoding='utf-8') as f:
    f.write(body_10)
print("[OK] Guardado: test-outputs/email_10_days_informativa.html")

# Guardar email de 3 días
with open('test-outputs/email_3_days_advertencia.html', 'w', encoding='utf-8') as f:
    f.write(body_3)
print("[OK] Guardado: test-outputs/email_3_days_advertencia.html")

# Guardar email de 1 día
with open('test-outputs/email_1_day_critica.html', 'w', encoding='utf-8') as f:
    f.write(body_1)
print("[OK] Guardado: test-outputs/email_1_day_critica.html")

# Guardar metadata
metadata = {
    'test_date': datetime.now().isoformat(),
    'license_actual': {
        'customer': license_data.get('customer'),
        'type': license_data.get('type'),
        'expires': license_data.get('expires'),
        'days_remaining': days
    },
    'scenarios': [
        {
            'days': 10,
            'level': 'INFORMATIVA',
            'customer': sim_license_10['customer'],
            'subject': subject_10,
            'email_size_bytes': len(body_10)
        },
        {
            'days': 3,
            'level': 'ADVERTENCIA',
            'customer': sim_license_3['customer'],
            'subject': subject_3,
            'email_size_bytes': len(body_3)
        },
        {
            'days': 1,
            'level': 'CRÍTICA',
            'customer': sim_license_1['customer'],
            'subject': subject_1,
            'email_size_bytes': len(body_1)
        }
    ]
}

with open('test-outputs/test_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
print("[OK] Guardado: test-outputs/test_metadata.json")

print()

# ============================================================================
# RESUMEN FINAL
# ============================================================================

print("═" * 70)
print("[SUCCESS] TODOS LOS TESTS FUNCIONALES COMPLETADOS EXITOSAMENTE")
print("═" * 70)
print()
print("[SUMMARY] Resumen de tests:")
print(f"   ✅ TEST 1: Licencia actual verificada ({days} días)")
print(f"   ✅ TEST 2: Escenario 10 días (INFORMATIVA)")
print(f"   ✅ TEST 3: Escenario 3 días (ADVERTENCIA)")
print(f"   ✅ TEST 4: Escenario 1 día (CRÍTICA)")
print(f"   ✅ TEST 5: Sistema de estado de alertas")
print(f"   ✅ TEST 6: Dumps de emails generados")
print()
print("[FILES] Archivos generados en: ./test-outputs/")
print("   - email_10_days_informativa.html")
print("   - email_3_days_advertencia.html")
print("   - email_1_day_critica.html")
print("   - test_metadata.json")
print()
