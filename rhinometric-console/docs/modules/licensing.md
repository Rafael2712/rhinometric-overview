# Module: Licensing

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Validate software license keys, enforce tier-based feature access, and provide a management interface for license operations. The module ensures only authorized deployments can access platform features.

## What It Does

- **License Server** (`license-server-v2`): Standalone container that validates license keys.
- **Hardware Fingerprinting**: Generates a unique hardware fingerprint from the deployment server's characteristics (CPU ID, MAC address, disk serial). License keys are bound to this fingerprint.
- **Tier System**: Three tiers with different feature sets:
  - **Community**: Basic monitoring, up to 10 services, no AI features.
  - **Professional**: AI anomaly detection, alerting, up to 50 services.
  - **Enterprise**: Full platform, unlimited services, SLO/SLA, RBAC, priority support.
- **Validation Flow**: Backend queries the license server on startup and periodically. Validation checks: key format, expiry date, hardware match, tier assignment.
- **License UI** (`license-ui`): Standalone web interface for license key entry and status display.
- **Feature Gating**: Backend API checks the active license tier before allowing access to tier-restricted features.

## What It Does Not Do

- Does not enforce license at the infrastructure level (containers always start).
- Does not support floating/concurrent license models.
- Does not phone home (no internet connectivity required after activation).
- Does not provide usage metering for billing purposes.
- Does not survive hardware changes without re-activation.
- Feature gating is not yet fully enforced across all modules.

## Architecture

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│  Backend API │──────▶│ License Server v2  │◀──────│  License UI  │
└──────────────┘       └───────────────────┘       └──────────────┘
                              │
                              ▼
                    Hardware Fingerprint
                    + License Key Store
```

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `license_key` | String | Encrypted license key |
| `tier` | Enum | community, professional, enterprise |
| `hardware_fingerprint` | String | Bound hardware ID |
| `issued_at` | DateTime | Key issue date |
| `expires_at` | DateTime | Key expiration date |
| `is_active` | Boolean | Whether currently valid |
| `features` | JSON | Tier-specific feature flags |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/license/status` | Current license status and tier |
| POST | `/api/license/activate` | Activate a license key |
| GET | `/api/license/features` | Available features for current tier |
| POST | `/api/license/validate` | Force re-validation |

## Infrastructure Components

| Component | Container | Port | Role |
|-----------|-----------|------|------|
| License Server | `license-server-v2` | 8200 | License key validation |
| License UI | `license-ui` | 8201 | License management interface |

## Dependencies

- **PostgreSQL**: Stores license records.
- **Backend API**: Queries license status for feature gating.
- **Hardware**: Fingerprint generation tied to host hardware.

## Frontend

- **Route:** `/licensing`
- **Key Features:** License status display, key activation form, tier information, feature availability matrix.

## Pre-Production Notes

The current Python license server will be replaced with a compiled Rust binary before commercial release to prevent reverse engineering. See PREPRODUCTION_ROADMAP.md for details.

## Known Limitations

1. Hardware fingerprint changes (e.g., NIC replacement) require re-activation.
2. Feature gating is not fully enforced across all modules.
3. No floating/concurrent license model.
4. No usage metering.
5. Python-based validator can be inspected — Rust replacement planned.

---

*Rhinometric Team — info@rhinometric.com*
