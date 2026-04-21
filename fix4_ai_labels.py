#!/usr/bin/env python3
# Phase 3 FIX-4: AI anomaly label consistency validation

with open('/tmp/detector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The fix is to add a comment and verification that labels match
# between _send_alert and _resolve_alert_in_am

old_resolve_section = '''    async def _resolve_alert_in_am(self, anomaly: 'AnomalyResult'):
        """
        Phase 3: Send resolution to Alertmanager when an anomaly is resolved.

        Builds a resolve payload with matching labels and endsAt = now,
        then posts it to AM so the alert transitions to 'resolved' state.
        """
        try:
            alert_builder = get_alert_builder()

            # Reconstruct the additional_labels that were used when firing
            additional_labels = {
                "priority": anomaly.metadata.get("priority", "medium"),
                "metric_type": "anomaly"
            }

            resolve_payload = alert_builder.build_resolve_alert(
                metric_name=anomaly.metric_name,
                severity=anomaly.severity,
                additional_labels=additional_labels
            )'''

new_resolve_section = '''    async def _resolve_alert_in_am(self, anomaly: 'AnomalyResult'):
        """
        Phase 3: Send resolution to Alertmanager when an anomaly is resolved.

        Builds a resolve payload with matching labels and endsAt = now,
        then posts it to AM so the alert transitions to 'resolved' state.
        
        Phase 3 FIX-4: Labels MUST match _send_alert exactly.
        """
        try:
            alert_builder = get_alert_builder()

            # Reconstruct additional_labels EXACTLY as in _send_alert (line ~497-500)
            # CRITICAL: These MUST match the fire labels or AM won't match the alert
            additional_labels = {
                "priority": anomaly.metadata.get("priority", "medium"),
                "metric_type": "anomaly"
            }
            
            # Verify metadata contains priority if it was set during fire
            if "priority" not in anomaly.metadata:
                logger.warning(
                    "[Resolve] Anomaly metadata missing 'priority' for %s - "
                    "label mismatch risk! Using default 'medium'",
                    anomaly.metric_name
                )

            resolve_payload = alert_builder.build_resolve_alert(
                metric_name=anomaly.metric_name,
                severity=anomaly.severity,
                additional_labels=additional_labels
            )'''

if old_resolve_section in content:
    content = content.replace(old_resolve_section, new_resolve_section)
    
    with open('/tmp/detector_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('FIX-4 APPLIED: Added label consistency validation and warning for AI anomaly resolution')
    print(f'File written to /tmp/detector_fixed.py')
else:
    print('ERROR: Could not find target section')
    # Check if function exists
    if '_resolve_alert_in_am' in content:
        print('Function exists but pattern did not match exactly')
    exit(1)
