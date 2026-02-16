#!/usr/bin/env python3
import os, json, hmac, hashlib, base64, uuid
from datetime import datetime, timedelta, timezone
import argparse

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--customer", required=True)
    p.add_argument("--type", choices=["trial", "annual", "permanent"], default="trial")
    p.add_argument("--days", type=int, default=15, help="Usado solo si type!=permanent")
    p.add_argument("--out", default="license.lic")
    args = p.parse_args()

    secret = os.environ.get("LICENSE_SECRET")
    if not secret:
        raise SystemExit("LICENSE_SECRET no está definida en el entorno")

    issued = datetime.now(timezone.utc)
    expires = None if args.type == "permanent" else (issued + timedelta(days=args.days))

    lic = {
        "id": str(uuid.uuid4()),
        "customer": args.customer,
        "type": args.type,
        "issued": issued.isoformat().replace("+00:00","Z"),
        "expires": None if expires is None else expires.isoformat().replace("+00:00","Z"),
        "hardware_lock": "",
        "features": {
            "max_nodes": 5 if args.type == "trial" else -1,
            "alerting": True,
            "dashboards": 10 if args.type == "trial" else -1,
            "retention_days": 7 if args.type == "trial" else 365
        }
    }

    # firma HMAC
    parts = [lic["id"], lic["customer"], lic["type"], lic["issued"], lic.get("expires") or "", lic.get("hardware_lock","")]
    canonical = "|".join(parts)
    mac = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).digest()
    lic["signature"] = b64url(mac)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(lic, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ Licencia generada en {args.out}")

if __name__ == "__main__":
    main()
