# Module: Licensing

**Version:** 2.7.0
**Classification:** Internal
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Validate software license keys, enforce tier-based feature access, and control the number of monitored services per deployment. The module ensures only authorized deployments can access platform features according to their license tier.

## What It Does

- **License Server** (`license-server-v2`): Standalone container that validates license keys.
- **Service-Based Model**: License tiers define the maximum number of monitored services:
  - **Community**: Basic monitoring, up to 10 services, no AI features.
  - **Professional**: AI anomaly detection, alerting, up to 50 services.
  - **Enterprise**: Full platform, unlimited services, SLO/SLA, RBAC, priority support.
- **Validation Flow**: Backend queries the license server on startup and periodically. Validation checks: key format, expiry date, tier assignment, service count within tier limit.
- **License UI** (`license-ui`): Standalone web interface for license key entry and status display.
- **Feature Gating**: Backend API checks the active license tier before allowing access to tier-restricted features.

## What It Does Not Do

- Does not enforce license at the infrastructure level (containers always start).
- Does not support floating/concurrent license models.
- Does not phone home (no internet connectivity required after activation).
- Does not provide usage metering for billing purposes.
- Feature gating is not yet fully enforced across all modules.

## Architecture

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│  Backend API │──────▶│ License Server v2  │◀──────│  License UI  │
└──────────────┘       └───────────────────┘       └──────────────┘
                              │
                              ▼
                    License Key Store
                    + Tier Configuration
                    + Service Count Limits
```

## Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `license_key` | String | Encrypted license key |
| `tier` | Enum | community, professional, enterprise |
| `max_services` | Integer | Maximum monitored services for this tier |
| `issued_at` | DateTime | Key issue date |
| `expires_at` | DateTime | Key expiration date |
| `is_active` | Boolean | Whether currently valid |
| `features` | JSON | Tier-specific feature flags |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/license/status` | Current license status and tier |
| POST | `/api/license/activate` | Activate a license key |
| GET | `/api/license/limits` | License limits and current usage per role |

## Infrastructure Components

| Component | Container | Port | Role |
|-----------|-----------|------|------|
| License Server | `license-server-v2` | 8200 | License key validation |
| License UI | `license-ui` | 8201 | License management interface |

## Dependencies

- **PostgreSQL**: Stores license records.
- **Backend API**: Queries license status for feature gating and service count enforcement.

## Frontend

- **Route:** `/license`
- **Key Features:** License status display, key activation form, tier information, feature availability matrix, current service count vs. tier limit.

## Pre-Production Notes

The current Python license server handles validation, tier enforcement, and service-count limits. Before commercial release, a compiled Rust binary will replace the Python implementation to provide tamper resistance and prevent reverse engineering. See PREPRODUCTION_ROADMAP.md for details.

## Known Limitations

1. Feature gating is not fully enforced across all modules.
2. No floating/concurrent license model.
3. No usage metering.
4. Python-based validator can be inspected — Rust replacement planned for tamper resistance.
5. Service count enforcement is validated at the API level; infrastructure containers always start regardless of license state.

---

*Rhinometric Team — info@rhinometric.com*
