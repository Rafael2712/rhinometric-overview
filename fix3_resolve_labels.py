#!/usr/bin/env python3
# Phase 3 FIX-3: SERVICE_DOWN resolve label validation and logging

with open('/tmp/alert_email_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_function = '''def resolve_alertmanager_alert(alert_name: str, entity_name: str,
                                severity: str, labels: dict = None):
    """
    Send endsAt to Alertmanager to stop it from repeating the alert.
    Called on resolve/dismiss to tell AM the alert is over.
    """
    def _do():
        try:
            import httpx
            from config import settings as _cfg
            now = datetime.now(timezone.utc)
            payload = [{
                "labels": labels or {
                    "alertname": alert_name,
                    "service_name": entity_name,
                    "severity": severity,
                    "source": "alert_policy",
                    "category": "external-services",
                },
                "endsAt": now.isoformat(),
                "startsAt": (now - __import__("datetime").timedelta(hours=1)).isoformat(),
            }]
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{_cfg.ALERTMANAGER_URL}/api/v2/alerts", json=payload)
                logger.info("[ALERT-EMAIL] Sent endsAt to AM for %s: status=%d", alert_name, resp.status_code)
        except Exception as exc:
            logger.warning("[ALERT-EMAIL] endsAt to AM failed (non-fatal): %s", exc)

    t = threading.Thread(target=_do, name="alert-am-resolve", daemon=True)'''

new_function = '''def resolve_alertmanager_alert(alert_name: str, entity_name: str,
                                severity: str, labels: dict = None):
    """
    Send endsAt to Alertmanager to stop it from repeating the alert.
    Called on resolve/dismiss to tell AM the alert is over.
    
    Phase 3 FIX-3: Added label validation and diagnostic logging.
    """
    def _do():
        try:
            import httpx
            import json
            from config import settings as _cfg
            now = datetime.now(timezone.utc)
            
            # Build labels - prefer passed labels over fallback
            if not labels:
                logger.warning(
                    "[ALERT-EMAIL] resolve_alertmanager_alert called without labels for %s - "
                    "building fallback labels. AM may not match if fire labels differed!",
                    alert_name
                )
                resolve_labels = {
                    "alertname": alert_name,
                    "service_name": entity_name,
                    "severity": severity,
                    "source": "alert_policy",
                    "category": "external-services",
                }
            else:
                resolve_labels = labels
            
            # Log labels for diagnosis
            logger.info(
                "[ALERT-EMAIL] Sending endsAt for %s with labels: %s",
                alert_name, json.dumps(resolve_labels)
            )
            
            payload = [{
                "labels": resolve_labels,
                "endsAt": now.isoformat(),
                "startsAt": (now - __import__("datetime").timedelta(hours=1)).isoformat(),
            }]
            
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{_cfg.ALERTMANAGER_URL}/api/v2/alerts", json=payload)
                if resp.status_code in (200, 201, 202):
                    logger.info(
                        "[ALERT-EMAIL] Successfully sent endsAt to AM for %s: status=%d",
                        alert_name, resp.status_code
                    )
                else:
                    logger.error(
                        "[ALERT-EMAIL] AM rejected endsAt for %s: status=%d, response=%s",
                        alert_name, resp.status_code, resp.text[:200]
                    )
        except Exception as exc:
            logger.warning("[ALERT-EMAIL] endsAt to AM failed (non-fatal): %s", exc)

    t = threading.Thread(target=_do, name="alert-am-resolve", daemon=True)'''

if old_function in content:
    content = content.replace(old_function, new_function)
    
    with open('/tmp/alert_email_service_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('FIX-3 APPLIED: Added label validation and diagnostic logging to resolve_alertmanager_alert')
    print(f'File written to /tmp/alert_email_service_fixed.py')
else:
    print('ERROR: Could not find target function')
    exit(1)
