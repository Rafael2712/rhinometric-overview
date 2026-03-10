"""
Alert Rules Hardening Script for External Services Monitoring.

Hardens all Grafana alert rules in the "External Services Alerts" group:
  - Sets noDataState to "Alerting" (was "OK" - silent data loss)
  - Confirms execErrState = "Alerting" on all rules
  - Adjusts pending durations per severity
  - Adds "External Service Checks Stale" alert (time() - last_check > 300s)

Requires: GRAFANA_URL, GRAFANA_USER, GRAFANA_PASSWORD env vars.
Usage:  GRAFANA_URL=http://grafana:3000 GRAFANA_USER=admin GRAFANA_PASSWORD=secret python3 harden_alert_rules.py
"""
import json
import os
import requests
import sys

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("GRAFANA_PASSWORD", "admin")
auth = (GRAFANA_USER, GRAFANA_PASSWORD)
HEADERS = {"Content-Type": "application/json"}
NAMESPACE_UID = os.environ.get("GRAFANA_FOLDER_UID", "ffeb5cpxpx0xse")
GROUP_NAME = "External Services Alerts"

# Step 1: Fetch current rules via Ruler API
print("[1/4] Fetching current alert rules...")
r = requests.get(f"{GRAFANA_URL}/api/ruler/grafana/api/v1/rules/{NAMESPACE_UID}/{GROUP_NAME}", auth=auth)
current = r.json()
rules = current.get("rules", [])
print(f"   Found {len(rules)} existing rules")

# Step 2: Update each rule via Provisioning API
print("[2/4] Hardening existing rules via Provisioning API...")

HARDENING = {
    "External Service Down":           {"noDataState": "Alerting", "execErrState": "Alerting", "for": "2m"},
    "External Service High Latency":   {"noDataState": "Alerting", "execErrState": "Alerting", "for": "5m"},
    "SSL Certificate Expiring Soon":   {"noDataState": "Alerting", "execErrState": "Alerting", "for": "10m"},
    "SSL Certificate Critical":        {"noDataState": "Alerting", "execErrState": "Alerting", "for": "10m"},
    "External Service Low Health Score":{"noDataState": "Alerting", "execErrState": "Alerting", "for": "5m"},
}

for rule in rules:
    ga = rule["grafana_alert"]
    title = ga["title"]
    uid = ga["uid"]

    if title not in HARDENING:
        print(f"   SKIP: {title}")
        continue

    h = HARDENING[title]
    old_nds = ga.get("no_data_state", "NoData")
    old_for = rule.get("for", "0s")

    pr = requests.get(f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{uid}", auth=auth)
    if pr.status_code != 200:
        print(f"   ERROR fetching {title}: {pr.status_code}")
        sys.exit(1)

    prov_rule = pr.json()
    prov_rule["noDataState"] = h["noDataState"]
    prov_rule["execErrState"] = h["execErrState"]
    prov_rule["for"] = h["for"]

    ur = requests.put(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{uid}",
        auth=auth, headers=HEADERS, json=prov_rule
    )

    parts = []
    if old_nds != h["noDataState"]: parts.append(f"noDataState: {old_nds}->{h['noDataState']}")
    if old_for != h["for"]: parts.append(f"for: {old_for}->{h['for']}")

    if ur.status_code in (200, 201):
        print(f"   OK {title}: {'; '.join(parts) if parts else 'confirmed'}")
    else:
        print(f"   FAIL {title}: {ur.status_code} {ur.text[:200]}")
        sys.exit(1)

# Step 3: Add stale alert
print("[3/4] Adding stale check alert...")
stale_exists = any(r["grafana_alert"]["title"] == "External Service Checks Stale" for r in rules)
if not stale_exists:
    stale_payload = {
        "title": "External Service Checks Stale",
        "ruleGroup": GROUP_NAME,
        "folderUID": NAMESPACE_UID,
        "condition": "threshold",
        "for": "5m",
        "noDataState": "Alerting",
        "execErrState": "Alerting",
        "isPaused": False,
        "labels": {"category": "external-services", "severity": "warning"},
        "annotations": {
            "description": "No health check recorded for {{ $labels.service_name }} in over 5 minutes. Scheduler may be stalled.",
            "summary": "Monitoring checks stale for {{ $labels.service_name }}"
        },
        "data": [
            {
                "refId": "A", "queryType": "",
                "relativeTimeRange": {"from": 600, "to": 0},
                "datasourceUid": "prometheus",
                "model": {
                    "expr": "time() - external_service_last_check_timestamp",
                    "instant": True, "intervalMs": 1000, "maxDataPoints": 43200,
                    "refId": "A"
                }
            },
            {
                "refId": "threshold", "queryType": "",
                "relativeTimeRange": {"from": 600, "to": 0},
                "datasourceUid": "__expr__",
                "model": {
                    "conditions": [{"evaluator": {"params": [300], "type": "gt"},
                                   "operator": {"type": "and"},
                                   "reducer": {"type": "last"}}],
                    "expression": "A", "intervalMs": 1000, "maxDataPoints": 43200,
                    "refId": "threshold", "type": "threshold"
                }
            }
        ]
    }
    cr = requests.post(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
        auth=auth, headers=HEADERS, json=stale_payload
    )
    if cr.status_code in (200, 201):
        print(f"   Created: External Service Checks Stale (uid={cr.json().get('uid','')})")
    else:
        print(f"   FAIL: {cr.status_code} {cr.text[:200]}")
        sys.exit(1)
else:
    print("   Already exists, skipping")

# Verify
print("\n[4/4] Verifying all rules...")
r = requests.get(f"{GRAFANA_URL}/api/ruler/grafana/api/v1/rules/{NAMESPACE_UID}/{GROUP_NAME}", auth=auth)
updated = r.json()
print(f"{'Rule':<45} {'noDataState':<15} {'execErrState':<15} {'for':<8}")
print("-" * 83)
for rule in updated.get("rules", []):
    ga = rule["grafana_alert"]
    print(f"{ga['title']:<45} {ga.get('no_data_state','?'):<15} {ga.get('exec_err_state','?'):<15} {rule.get('for','?'):<8}")

print(f"\nTotal rules: {len(updated.get('rules',[]))}")
print("Done. All alert rules hardened successfully.")
