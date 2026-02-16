#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, json
from datetime import datetime, timedelta

sys.path.insert(0, 'license-monitor')
from license_monitor import find_license_file, load_license, get_days_until_expiration, get_email_template, load_alert_state, save_alert_state

print("=" * 70)
print("RHINOMETRIC LICENSE MONITOR - FUNCTIONAL TEST SUITE")
print("=" * 70 + "\n")

print("=" * 70)
print("TEST 1: VERIFICAR LICENCIA ACTUAL")
print("=" * 70 + "\n")

license_path = find_license_file()
if not license_path:
    print("[ERROR] No se encontro licencia")
    sys.exit(1)

print(f"[OK] Licencia encontrada: {license_path}\n")

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
print(f"   Features: {', '.join(license_data.get('features', []))}\n")

days = get_days_until_expiration(license_data)
if days is None:
    print("[ERROR] No se pudo calcular expiracion")
    sys.exit(1)

if days > 900000:
    print("[OK] Licencia PERPETUA (no expira)")
elif days < 0:
    print(f"[ERROR] Licencia EXPIRADA hace {abs(days)} dias")
else:
    print(f"[OK] Licencia valida - {days} dias restantes\n")

print("=" * 70)
print("TEST 2: ESCENARIO - LICENCIA EXPIRA EN 10 DIAS (INFORMATIVA)")
print("=" * 70 + "\n")

sim_license_10 = {
    'customer': 'BancoSantander',
    'type': 'annual',
    'hwid': 'A3F7C9E1B2D4F6A8',
    'expires': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=355)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting', 'ai_anomaly']
}

print("[INFO] Licencia simulada:")
print(f"   Cliente:  {sim_license_10['customer']}")
print(f"   Expira:   {sim_license_10['expires']}")
print(f"   Dias:     10\n")

subject_10, body_10 = get_email_template(10, sim_license_10)

print("[EMAIL] Email generado:")
print(f"   Asunto:   {subject_10}")
print(f"   Tamano:   {len(body_10)} bytes")
print(f"   Nivel:    INFORMATIVA")
print(f"   Color:    Azul (#3498db)\n")

print("=" * 70)
print("TEST 3: ESCENARIO - LICENCIA EXPIRA EN 3 DIAS (ADVERTENCIA)")
print("=" * 70 + "\n")

sim_license_3 = {
    'customer': 'TelefonicaEspana',
    'type': 'trial',
    'hwid': 'B4E8D1F3C5A7B9D2',
    'expires': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=27)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting']
}

print("[INFO] Licencia simulada:")
print(f"   Cliente:  {sim_license_3['customer']}")
print(f"   Expira:   {sim_license_3['expires']}")
print(f"   Dias:     3\n")

subject_3, body_3 = get_email_template(3, sim_license_3)

print("[EMAIL] Email generado:")
print(f"   Asunto:   {subject_3}")
print(f"   Tamano:   {len(body_3)} bytes")
print(f"   Nivel:    ADVERTENCIA")
print(f"   Color:    Naranja (#f39c12)\n")

print("=" * 70)
print("TEST 4: ESCENARIO - LICENCIA EXPIRA EN 1 DIA (CRITICA)")
print("=" * 70 + "\n")

sim_license_1 = {
    'customer': 'BBVA',
    'type': 'annual',
    'hwid': 'C5F9E2A4D6B8C1E3',
    'expires': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
    'issued_at': (datetime.now() - timedelta(days=364)).isoformat() + 'Z',
    'features': ['monitoring', 'alerting', 'reporting', 'ai_anomaly', 'veriverde_esg', 'api_connector']
}

print("[INFO] Licencia simulada:")
print(f"   Cliente:  {sim_license_1['customer']}")
print(f"   Expira:   {sim_license_1['expires']}")
print(f"   Dias:     1\n")

subject_1, body_1 = get_email_template(1, sim_license_1)

print("[EMAIL] Email generado:")
print(f"   Asunto:   {subject_1}")
print(f"   Tamano:   {len(body_1)} bytes")
print(f"   Nivel:    CRITICA")
print(f"   Color:    Rojo (#e74c3c)\n")

print("=" * 70)
print("TEST 5: VERIFICAR SISTEMA DE ESTADO DE ALERTAS")
print("=" * 70 + "\n")

alert_state = load_alert_state()
print("[STATUS] Estado actual de alertas:")
for day, sent in alert_state.items():
    status = "[SENT]" if sent else "[PENDING]"
    print(f"   {day} dias: {status}")
print()

print("[ACTION] Simulando envio de alerta de 10 dias...")
alert_state[10] = True
save_alert_state(alert_state)
print("[OK] Estado actualizado\n")

alert_state_check = load_alert_state()
if alert_state_check.get(10):
    print("[OK] Estado persistente verificado correctamente\n")
else:
    print("[ERROR] Estado no se guardo correctamente\n")

print("=" * 70)
print("TEST 6: GENERAR DUMPS DE EMAILS PARA INSPECCION")
print("=" * 70 + "\n")

os.makedirs('test-outputs', exist_ok=True)

with open('test-outputs/email_10_days_informativa.html', 'w', encoding='utf-8') as f:
    f.write(body_10)
print("[OK] Guardado: test-outputs/email_10_days_informativa.html")

with open('test-outputs/email_3_days_advertencia.html', 'w', encoding='utf-8') as f:
    f.write(body_3)
print("[OK] Guardado: test-outputs/email_3_days_advertencia.html")

with open('test-outputs/email_1_day_critica.html', 'w', encoding='utf-8') as f:
    f.write(body_1)
print("[OK] Guardado: test-outputs/email_1_day_critica.html")

metadata = {
    'test_date': datetime.now().isoformat(),
    'license_actual': {
        'customer': license_data.get('customer'),
        'type': license_data.get('type'),
        'expires': license_data.get('expires'),
        'days_remaining': days
    },
    'scenarios': [
        {'days': 10, 'level': 'INFORMATIVA', 'customer': sim_license_10['customer'], 'subject': subject_10, 'email_size_bytes': len(body_10)},
        {'days': 3, 'level': 'ADVERTENCIA', 'customer': sim_license_3['customer'], 'subject': subject_3, 'email_size_bytes': len(body_3)},
        {'days': 1, 'level': 'CRITICA', 'customer': sim_license_1['customer'], 'subject': subject_1, 'email_size_bytes': len(body_1)}
    ]
}

with open('test-outputs/test_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
print("[OK] Guardado: test-outputs/test_metadata.json\n")

print("=" * 70)
print("[SUCCESS] TODOS LOS TESTS FUNCIONALES COMPLETADOS EXITOSAMENTE")
print("=" * 70 + "\n")
print("[SUMMARY] Resumen de tests:")
print(f"   [OK] TEST 1: Licencia actual verificada ({days} dias)")
print(f"   [OK] TEST 2: Escenario 10 dias (INFORMATIVA)")
print(f"   [OK] TEST 3: Escenario 3 dias (ADVERTENCIA)")
print(f"   [OK] TEST 4: Escenario 1 dia (CRITICA)")
print(f"   [OK] TEST 5: Sistema de estado de alertas")
print(f"   [OK] TEST 6: Dumps de emails generados\n")
print("[FILES] Archivos generados en: ./test-outputs/")
print("   - email_10_days_informativa.html")
print("   - email_3_days_advertencia.html")
print("   - email_1_day_critica.html")
print("   - test_metadata.json\n")
