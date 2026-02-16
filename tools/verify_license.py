#!/usr/bin/env python3
import os, json, hmac, hashlib, base64, sys

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "security/licensing/license.lic"
    secret = os.environ.get("LICENSE_SECRET")
    if not secret:
        print("LICENSE_SECRET no está definida"); return 2
    with open(path, encoding="utf-8") as f:
        lic = json.load(f)
    parts = [lic["id"], lic["customer"], lic["type"], lic["issued"], lic.get("expires") or "", lic.get("hardware_lock","")]
    canonical = "|".join(parts)
    mac = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).digest()
    expected = b64url(mac)
    if lic.get("signature") == expected:
        print("✅ Firma válida"); return 0
    else:
        print("❌ Firma inválida"); return 1

if __name__ == "__main__":
    sys.exit(main())
