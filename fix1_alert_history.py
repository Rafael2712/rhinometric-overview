#!/usr/bin/env python3
# Phase 3 FIX-1: Alert History dual-table query
import re

with open('/tmp/alerts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new implementation
new_implementation = '''@router.get("/history")
async def get_alert_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category (e.g. external-services)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status (firing/resolved)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Get alert history from the database, newest first.
    
    Phase 3 FIX-1: Query BOTH alert_history (webhook) AND alert_events 
    (policy/assertion/anomaly) to provide complete historical visibility.
    """
    # Query alert_history (Grafana webhook alerts)
    hist_query = db.query(AlertHistory)
    if category:
        hist_query = hist_query.filter(AlertHistory.category == category)
    if severity:
        hist_query = hist_query.filter(AlertHistory.severity == severity)
    if service_name:
        hist_query = hist_query.filter(AlertHistory.service_name == service_name)
    if status:
        hist_query = hist_query.filter(AlertHistory.status == status)
    hist_records = hist_query.order_by(AlertHistory.created_at.desc()).all()

    # Query alert_events (operational alerts: policy, assertion, anomaly)
    # Only show resolved/dismissed in history (active alerts are in /alerts)
    event_query = db.query(AlertEvent).filter(
        AlertEvent.status.in_(["resolved", "dismissed"])
    )
    if category:
        event_query = event_query.filter(AlertEvent.entity_type == category)
    if severity:
        event_query = event_query.filter(AlertEvent.severity == severity)
    if service_name:
        event_query = event_query.filter(AlertEvent.entity_name == service_name)
    # status filter maps to event.status
    if status and status in ("resolved", "dismissed", "firing"):
        event_query = event_query.filter(AlertEvent.status == status)
    
    event_records = event_query.order_by(AlertEvent.started_at.desc()).all()

    # Merge both sources
    all_alerts = []
    seen_fingerprints = set()
    
    # Format alert_history records
    for r in hist_records:
        fp = r.fingerprint or ""
        if fp and fp in seen_fingerprints:
            continue
        if fp:
            seen_fingerprints.add(fp)
        all_alerts.append({
            "id": r.id,
            "fingerprint": fp,
            "alertname": r.alertname,
            "status": r.status,
            "severity": r.severity,
            "category": r.category,
            "service_name": r.service_name,
            "summary": r.summary,
            "description": r.description,
            "value": r.value,
            "starts_at": r.starts_at.isoformat() if r.starts_at else None,
            "ends_at": r.ends_at.isoformat() if r.ends_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "source": "webhook"
        })
    
    # Format alert_events records
    for e in event_records:
        fp = e.fingerprint or ""
        if fp and fp in seen_fingerprints:
            continue
        if fp:
            seen_fingerprints.add(fp)
        all_alerts.append({
            "id": str(e.id),
            "fingerprint": fp,
            "alertname": e.alert_name or "",
            "status": e.status,
            "severity": e.severity or "warning",
            "category": e.entity_type or "",
            "service_name": e.entity_name or "",
            "summary": e.summary or "",
            "description": (e.annotations.get("description", "") 
                           if e.annotations and isinstance(e.annotations, dict) else ""),
            "value": None,
            "starts_at": e.started_at.isoformat() if e.started_at else None,
            "ends_at": e.ended_at.isoformat() if e.ended_at else None,
            "created_at": e.started_at.isoformat() if e.started_at else None,
            "source": e.source or "alert_policy"
        })
    
    # Sort by created_at/starts_at descending
    all_alerts.sort(
        key=lambda x: x.get("created_at") or x.get("starts_at") or "", 
        reverse=True
    )
    
    # Apply pagination
    total = len(all_alerts)
    paginated = all_alerts[offset:offset+limit]

    return {
        "total": total,
        "alerts": paginated,
    }'''

# Find and replace the function
# Find the get_alert_history function
start_marker = '@router.get("/history")'
end_marker = '# ================================================================\n# GET /api/alerts/noise-filter/stats'

start_pos = content.find(start_marker)
end_pos = content.find(end_marker, start_pos)

if start_pos == -1 or end_pos == -1:
    print('ERROR: Could not find function boundaries')
    exit(1)

# Replace the function
new_content = content[:start_pos] + new_implementation + '\n\n' + content[end_pos:]

with open('/tmp/alerts_fixed.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('FIX-1 APPLIED: Alert History now queries BOTH alert_history AND alert_events')
print(f'File written to /tmp/alerts_fixed.py')
print(f'Total lines: {len(new_content.splitlines())}')
