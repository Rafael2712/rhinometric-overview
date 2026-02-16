# LICENSE_VALIDATION_FLOW.md — Rhinometric License Validation

## 1. Overview

Rhinometric validates its license at VM/stack startup using
`rhino-lic`, a statically-linked Rust binary that performs
Ed25519 signature verification, date range checks, and machine
fingerprint binding.

**If the license is invalid, the Docker stack will NOT start.**

---

## 2. File Locations

| File | Path | Purpose |
|------|------|---------|
| License file | `/opt/rhinometric/license.key` | Signed JSON license (per-tenant) |
| Validator binary | `/usr/local/bin/rhino-lic` | Ed25519 license validator (1.1 MB) |
| Startup script | `/opt/rhinometric/start-rhinometric.sh` | Validates license → starts Docker stack |
| Compose file | `/opt/rhinometric/docker-compose-v2.5.0-SECURE.yml` | Docker Compose for the full stack |
| Issuer keys | `/opt/rhinometric/rust-licenses/keys/` | Ed25519 keypair (private key = issuer only) |

---

## 3. License File Format

The license is a JSON file (`license.key`) with this structure:

```json
{
  "payload": {
    "version": 1,
    "tenant_id": "rhinometric-prod",
    "customer": "Rhinometric Production",
    "plan": "enterprise",
    "max_hosts": 100,
    "issued_at": "2026-02-14T11:51:00+00:00",
    "expires_at": "2027-12-31T23:59:59Z",
    "fingerprint": "sha256:<64-hex-chars>",
    "features": ["monitoring", "alerting", "anomaly-detection"]
  },
  "signature": "<base64-ed25519-signature>"
}
```

The `signature` is computed over the **canonical JSON serialisation**
of `payload` (via `serde_json::to_string`), using Ed25519.

---

## 4. Validation Flow

```
┌───────────────────────────────────────────────────┐
│             start-rhinometric.sh                  │
│                                                   │
│  1. Does /opt/rhinometric/license.key exist?      │
│     NO  → print error, exit 1                     │
│     YES → continue                                │
│                                                   │
│  2. rhino-lic validate /opt/rhinometric/license.key│
│     │                                             │
│     ├─ exit 0  → License VALID                    │
│     │   → docker-compose up -d                    │
│     │                                             │
│     ├─ exit 1  → Invalid signature (tampered)     │
│     ├─ exit 2  → Expired or not yet valid         │
│     ├─ exit 3  → Fingerprint mismatch             │
│     └─ exit 4  → Parse/IO error                   │
│         → print reason, do NOT start stack        │
└───────────────────────────────────────────────────┘
```

### What `rhino-lic validate` checks (in order):

1. **Ed25519 signature** — Verifies signature against the
   embedded public key. Prevents tampering with any field.

2. **Date range** — `issued_at <= now <= expires_at`.
   Prevents use of not-yet-valid or expired licenses.

3. **Machine fingerprint** — `SHA-256(machine-id + ":" + MAC)`.
   Binds the license to a specific physical or virtual host.

---

## 5. Startup Usage

### Normal start (with license validation):

```bash
cd /opt/rhinometric
./start-rhinometric.sh
```

### Direct docker-compose (bypass validation — NOT recommended):

```bash
cd /opt/rhinometric
docker-compose -f docker-compose-v2.5.0-SECURE.yml up -d
```

---

## 6. Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | License valid | Stack starts normally |
| 1 | Invalid Ed25519 signature | License file may be tampered. Re-issue. |
| 2 | License expired or not yet valid | Request license renewal. |
| 3 | Machine fingerprint mismatch | License was issued for a different host. |
| 4 | Parse error / IO failure | Check file exists and is valid JSON. |

---

## 7. License Renewal

When a license expires or a tenant migrates to a new host:

### Step 1: Get the new machine's fingerprint

```bash
rhino-lic fingerprint
# Output: sha256:3c07c19281a4a79ed20af5f77a7bc1cd0b777d9baf349a54b92c268732a61933
```

### Step 2: Issue a new license (on the issuer machine)

```bash
rhino-lic issue \
  --tenant-id <tenant-id> \
  --customer "<Customer Name>" \
  --plan <plan> \
  --max-hosts <N> \
  --expires-at <ISO-8601-date> \
  --fingerprint-value "sha256:<hex>" \
  --features monitoring,alerting \
  --privkey /path/to/license.key \
  --out new-license.json
```

### Step 3: Deploy to the target VM

```bash
scp new-license.json root@<vm-ip>:/opt/rhinometric/license.key
```

### Step 4: Restart the stack

```bash
ssh root@<vm-ip> "cd /opt/rhinometric && ./start-rhinometric.sh"
```

---

## 8. Troubleshooting

### "License file not found"

```bash
ls -la /opt/rhinometric/license.key
# If missing, obtain a license from your administrator
```

### "Machine fingerprint mismatch"

```bash
# Check what the VM reports:
rhino-lic fingerprint

# Check what the license expects:
python3 -c "import json; print(json.load(open('/opt/rhinometric/license.key'))['payload']['fingerprint'])"

# If they differ, the license was issued for a different host.
# Re-issue with the correct fingerprint.
```

### "License has expired"

```bash
rhino-lic validate /opt/rhinometric/license.key
# Shows expires_at in the output JSON
# Request a renewal with a future expires_at
```

### "Invalid Ed25519 signature"

The license file has been modified after signing. Possible causes:
- Manual editing of the JSON
- File corruption during transfer
- Mismatched public/private keys

Re-issue the license from the original issuer.

---

## 9. Security Notes

- The **private key** is NEVER stored on client VMs.
  Only the issuer machine has the private key.
- The **public key** is embedded in the `rhino-lic` binary
  at compile time as `LICENSE_PUBKEY: [u8; 32]`.
- The license file can be read by anyone, but cannot be
  modified without invalidating the signature.
- Machine fingerprints are derived from `/etc/machine-id`
  and the primary **physical** network interface MAC address.
  Virtual interfaces (`docker0`, `br-*`, `veth*`, etc.) are
  excluded to ensure fingerprint stability across Docker
  restarts and bridge recreations.
- The `.gitignore` in the Rust project excludes `*.key` files.
