# Rhinometric Platform — Logs Explorer & Session Stability

**Release:** v2.7.2
**Date:** April 2026

---

## Overview

This release delivers significant improvements to the Rhinometric Console's **Log Explorer** module and resolves a **session stability** issue that affected user experience during extended usage sessions.

---

## Log Explorer Enhancements

### Smarter Filter Organization

The Log Explorer now organizes filters into two intuitive tiers:

- **Quick Filters** — The most frequently used filters (service type, service name, severity level) are prominently placed for fast access.
- **Advanced Filters** — Detailed filtering options (event type, HTTP status code, HTTP method, URL path) are available in a secondary row for deeper investigation.

This layout reduces visual clutter and helps operators find relevant logs faster.

### Canonical Severity Levels

The severity filter now displays all standard log levels — **fatal, error, warn, info, debug, and unknown** — regardless of whether those levels are currently present in the data. This ensures consistent filtering behavior across different time windows and services.

Previously, only severity levels present in the current dataset were shown, which could be confusing when investigating specific error types.

### Optimized Defaults

Default query parameters have been tuned for typical operational workflows:

- **Time window:** 1 hour (previously 3 hours)
- **Result limit:** 100 entries (previously 500)
- **Available time ranges:** 15 minutes, 1 hour, 6 hours, 24 hours, 7 days

These defaults reduce initial load time and API response size while still covering the most common investigation scenarios.

### Service Type Classification

Each log entry is now automatically classified by service type (HTTP API, Web Application, Database, Collector), enabling operators to quickly filter logs by the kind of infrastructure component that generated them.

---

## Platform Session Stability

### Resolved: Session Interruption After Inactivity

A stability issue was identified and resolved where the platform would lose the active session after a period of inactivity (~60–90 minutes), requiring users to log in again even though their session had not expired.

**Impact:**
- Users no longer experience unexpected logouts during normal work sessions
- The platform handles browser tab restoration gracefully
- Error bursts on protected endpoints after inactivity are eliminated

**User-facing behavior:**
- Sessions persist correctly for their full configured duration (24 hours)
- Returning to an inactive tab resumes the session seamlessly
- If a session has genuinely expired, the platform redirects cleanly to the login page without error messages

---

## Collector v1.1.0

The Rhinometric Telemetry Collector has been repackaged for production customer delivery:

- **Clear startup validation** — Missing configuration is reported immediately with actionable error messages
- **Operational visibility** — Startup banner shows version, connection status, and collection interval
- **Per-cycle reporting** — Each collection cycle reports signal-level results (metrics, logs, traces) with status and timing
- **Flexible configuration** — Environment variables, configuration files, and sensible defaults with clear precedence
- **Production-ready Docker image** — Health checks, proper metadata, and non-root execution

---

## Compatibility

- **Backend:** No API changes. Fully backward compatible.
- **Frontend:** UI improvements only. No workflow changes required.
- **Collector:** New version (v1.1.0) is backward compatible with existing installations.

---

## What's Next

- Enhanced dashboards with real-time service health visualization
- Expanded anomaly detection coverage
- Advanced log correlation with traces and metrics

---

*Rhinometric — Observability Platform*
*For more information: info@rhinometric.com*
