#!/usr/bin/env python3
import os, sys, json, hmac, hashlib, base64
from datetime import datetime, timezone

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def parse_isoz(s: str):
    if not s: return None
    # soporta "2025-09-19T12:00:00Z"
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def main():
    if len(sys.argv) < 2:
        print("Uso: validator.py <ruta_licencia>", file=sys.stderr); return 2
    lic_path = sys.argv[1]
    secret = os.environ.get("LICENSE_SECRET")
    if not secret:
        print("LICENSE_SECRET no está definida", file=sys.stderr); return 2

    lic = json.load(open(lic_path, encoding="utf-8"))

    # 1) Firma
    parts = [
        lic["id"], lic["customer"], lic["type"], lic["issued"],
        lic.get("expires") or "", lic.get("hardware_lock","")
    ]
    canonical = "|".join(parts)
    mac = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).digest()
    if lic.get("signature") != b64url(mac):
        print("❌ Licencia inválida (firma)", file=sys.stderr); return 1

    # 2) Expiración (si aplica)
    expires = parse_isoz(lic.get("expires"))
    if expires is not None and datetime.now(timezone.utc) > expires:
        print("❌ Licencia expirada", file=sys.stderr); return 1

    # (opcional) 3) hardware_lock si decides aplicarlo
    # hw = obtener_huella_hw() ; if lic.get("hardware_lock") and lic["hardware_lock"] != hw: ...

    print("✅ Licencia válida")
    return 0

if __name__ == "__main__":
    sys.exit(main())

