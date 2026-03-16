# Rhinometric — Pre-Production Roadmap

**Version:** 2.7.0  
**Date:** March 2026  
**Classification:** Internal — Confidential  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Overview

This document tracks the remaining items required before Rhinometric can be released to market as a commercial product. Each item includes its current status, priority, and estimated effort.

---

## 1. Platform Stability (P0 — Must Have)

### 1.1 Service Monitoring Redesign
**Status:** Not Started  
**Priority:** P0  
**Effort:** 2–3 weeks

The current Services page is designed for 10–30 services. For commercial viability, it must support 100–200 services with:
- Pagination and search
- Bulk operations (enable/disable, delete)
- Group/tag-based filtering
- Performance optimization for large service lists
- Import/export service definitions (CSV/JSON)

### 1.2 Home Dashboard — Configurable Widgets
**Status:** Not Started  
**Priority:** P0  
**Effort:** 1–2 weeks

The Home page currently shows hardcoded KPI cards. It needs:
- Configurable widget layout
- User-selectable metrics
- Role-based dashboard views
- Persistent layout preferences per user

### 1.3 Close Technical Debt
**Status:** In Progress  
**Priority:** P0  
**Effort:** Ongoing

- [ ] Database migration system (Alembic setup)
- [ ] Error handling standardization across all routers
- [ ] API response schema validation (Pydantic models for all responses)
- [ ] Remove hardcoded URLs and magic numbers
- [ ] Standardize logging format across all services

---

## 2. Licensing & Distribution (P0)

### 2.1 Rust Binary License Validator
**Status:** Not Started  
**Priority:** P0  
**Effort:** 2–3 weeks

Replace the current Python license validator with a compiled Rust binary that:
- Validates license keys with hardware fingerprinting
- Cannot be easily reverse-engineered
- Works offline (no phone-home required)
- Integrates as a sidecar or library

### 2.2 Ansible-Based Enterprise Installer
**Status:** Not Started  
**Priority:** P0  
**Effort:** 2 weeks

Replace manual Docker Compose deployment with:
- Ansible playbooks for automated installation
- OS compatibility checks (Ubuntu 22.04/24.04, Rocky Linux 8/9)
- Pre-flight validation (resources, ports, dependencies)
- Upgrade path from previous versions
- Rollback capability

### 2.3 License Tier Enforcement
**Status:** Partial  
**Priority:** P0  
**Effort:** 1 week

Current state: License server validates keys and assigns tiers. Missing:
- [ ] Feature gating enforcement across all modules
- [ ] Graceful degradation when license expires
- [ ] Usage metrics collection for metering

---

## 3. Testing & Quality (P0)

### 3.1 Test Coverage for Core Modules
**Status:** Not Started  
**Priority:** P0  
**Effort:** 3–4 weeks

- [ ] Unit tests for backend services (target: 80% coverage)
- [ ] Integration tests for API endpoints
- [ ] E2E tests for critical user flows (login → anomaly → incident)
- [ ] Load tests for API endpoints under stress

### 3.2 Load & Performance Testing
**Status:** Not Started  
**Priority:** P0  
**Effort:** 1 week

Validate platform behavior with:
- 100+ monitored services
- 1,000+ concurrent metric streams
- 50+ active anomaly groups
- 10+ concurrent users
- 7-day continuous operation stability test

### 3.3 Production Deployment Validation
**Status:** Partial  
**Priority:** P0  
**Effort:** 1 week

The platform is currently deployed on a single staging server. Before release:
- [ ] Clean production installation from scratch
- [ ] Document all environment variables
- [ ] Validate upgrade from v2.5 → v2.7
- [ ] Backup and restore procedures
- [ ] Disaster recovery documentation

---

## 4. Security Hardening (P1)

### 4.1 RBAC Hardening & Audit Trail
**Status:** Partial  
**Priority:** P1  
**Effort:** 1–2 weeks

Current state: 4 roles are implemented. Missing:
- [ ] Complete audit trail for all admin operations
- [ ] Resource-level permissions (per-service, per-dashboard)
- [ ] API key authentication (for programmatic access)
- [ ] Session management (concurrent session limits)

### 4.2 Secret Management
**Status:** Not Started  
**Priority:** P1  
**Effort:** 1 week

- [ ] Move secrets from `.env` to encrypted vault (HashiCorp Vault or SOPS)
- [ ] Rotate JWT secret key mechanism
- [ ] Database credential rotation

---

## 5. Documentation (P1)

### 5.1 Complete Documentation Pack
**Status:** In Progress  
**Priority:** P1  
**Effort:** 1 week

- [x] Functional platform overview
- [x] Technical platform overview
- [x] Module-level documentation
- [x] Public repository updated
- [x] Release notes
- [ ] Operations manual (backup, restore, upgrade, troubleshooting)
- [ ] API reference documentation (OpenAPI/Swagger)
- [ ] User manual with screenshots
- [ ] Video walkthroughs

### 5.2 Documentation Site
**Status:** Not Started  
**Priority:** P1  
**Effort:** 1 week

Define and build the final documentation hosting:
- Options: GitBook, Docusaurus, MkDocs, or self-hosted
- Must support versioning, search, and multi-language

---

## 6. Platform Expansion (P2)

### 6.1 Additional Notification Channels
**Status:** Not Started  
**Priority:** P2  
- [ ] Microsoft Teams
- [ ] PagerDuty
- [ ] OpsGenie
- [ ] SMS (Twilio)
- [ ] Custom webhook

### 6.2 Dashboard Builder v1
**Status:** Not Started  
**Priority:** P2  
- [ ] Native dashboard creation (not Grafana-dependent)
- [ ] Drag-and-drop widget placement
- [ ] Template gallery

### 6.3 SSO / LDAP / SAML
**Status:** Not Started  
**Priority:** P2  
- [ ] LDAP/Active Directory integration
- [ ] SAML 2.0 IdP support
- [ ] OAuth 2.0 / OIDC

### 6.4 Multi-Tenant Architecture
**Status:** Not Started  
**Priority:** P2  
- [ ] Tenant isolation at database level
- [ ] Per-tenant branding
- [ ] Cross-tenant admin views

---

## Progress Summary

| Category | Items | Done | In Progress | Not Started |
|----------|-------|------|------------|-------------|
| Platform Stability | 3 | 0 | 1 | 2 |
| Licensing & Distribution | 3 | 0 | 0 | 3 |
| Testing & Quality | 3 | 0 | 1 | 2 |
| Security Hardening | 2 | 0 | 0 | 2 |
| Documentation | 2 | 0 | 1 | 1 |
| Platform Expansion | 4 | 0 | 0 | 4 |
| **Total** | **17** | **0** | **3** | **14** |

**Estimated total effort to market readiness:** 12–16 weeks

---

*Document generated by Rhinometric Team — info@rhinometric.com*  
*Last updated: March 2026*
