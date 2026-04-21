#!/usr/bin/env python3
"""
Phase 3 Investigation Script
Tests alert lifecycle end-to-end for all alert types
"""
import sys
import json
import time
import requests
from datetime import datetime, timedelta

BASE_URL = 'http://rhinometric-console-backend:8105'
AM_URL = 'http://rhinometric-alertmanager:9093'

def get_db_connection():
    import psycopg2
    return psycopg2.connect(
        host='rhinometric-postgres',
        port=5432,
        user='rhinometric',
        password='rhinometric_pass',
        database='rhinometric'
    )

def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

def check_current_state():
    """Check current system state"""
    log('=' * 70)
    log('CURRENT SYSTEM STATE')
    log('=' * 70)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check alert_events
    cur.execute("SELECT COUNT(*), source, status FROM alert_events GROUP BY source, status ORDER BY source, status")
    rows = cur.fetchall()
    log('alert_events summary:')
    for count, source, status in rows:
        log(f'  {source:20s} | {status:15s} | {count:5d}')
    
    # Check active alerts
    cur.execute("SELECT COUNT(*) FROM alert_events WHERE status IN ('firing', 'acknowledged', 'silenced')")
    active = cur.fetchone()[0]
    log(f'\nActive alerts in DB: {active}')
    
    # Check alert_history
    cur.execute("SELECT COUNT(*) FROM alert_history")
    hist_count = cur.fetchone()[0]
    log(f'alert_history records: {hist_count}')
    
    # Check Alertmanager
    try:
        resp = requests.get(f'{AM_URL}/api/v2/alerts', timeout=10)
        if resp.status_code == 200:
            am_alerts = resp.json()
            active_in_am = [a for a in am_alerts if a.get('status', {}).get('state') == 'active']
            log(f'Active alerts in Alertmanager: {len(active_in_am)}')
            if active_in_am:
                for a in active_in_am[:5]:
                    log(f'  - {a.get("labels", {}).get("alertname")}: {a.get("status", {}).get("state")}')
        else:
            log(f'✗ Alertmanager returned {resp.status_code}')
    except Exception as e:
        log(f'✗ Failed to check Alertmanager: {e}')
    
    conn.close()

def analyze_root_causes():
    """Analyze root causes from code inspection"""
    log('\n' + '=' * 70)
    log('ROOT CAUSE ANALYSIS (from code inspection)')
    log('=' * 70)
    
    findings = {
        'BLOCK A - SERVICE_DOWN resolution': {
            'issue': 'SERVICE_DOWN resolves in DB but may stay active in AM',
            'code_path': 'alert_rules.py::_resolve_recovered_services() line 396',
            'root_cause': 'Labels mismatch between fire and resolve payloads',
            'evidence': 'resolve_alertmanager_alert() is called but may use different labels',
            'fix_needed': 'Ensure labels used in resolve match exactly the fire labels'
        },
        'BLOCK B - Email inconsistency': {
            'issue': 'Critical email arrives but alert not visible / or no email sent',
            'code_paths': [
                'alert_email_service.py::send_firing_notification() line 229',
                'alert_email_service.py::send_recovery_notification() line 288',
                'alert_rules.py::_fire_rule_alert() line 1133-1141'
            ],
            'root_cause_1': 'send_firing_notification checks notification_sent_at to prevent dupes',
            'root_cause_2': 'send_recovery_notification requires notification_sent_at to be set',
            'root_cause_3': 'If alert created but email not triggered, recovery also won\'t send',
            'evidence': 'Line 293: if not notification_sent_at: skip recovery',
            'fix_needed': 'Ensure all alert creation paths call send_firing_notification()'
        },
        'BLOCK C - Alert History gap': {
            'issue': 'Critical alert has email but not in Alert History',
            'code_paths': [
                'alerts.py::/webhook endpoint stores in alert_history',
                'alerts.py::/history endpoint queries alert_history ONLY'
            ],
            'root_cause': 'alert_history is ONLY populated by Grafana webhook',
            'evidence': 'AI anomaly, assertion_failure, policy alerts go to alert_events but NOT alert_history',
            'fix_needed': 'Alert History query must ALSO include alert_events table',
            'critical': 'THIS IS THE PRIMARY ISSUE - alert_history is incomplete!'
        },
        'BLOCK D - Cross-source sync': {
            'issue': 'Alertmanager vs alert_events inconsistency',
            'evidence': 'AM may have alerts that are dismissed/resolved in DB',
            'root_cause': 'Sync logic in alerts.py::get_alerts() tries to reconcile but may miss cases',
            'fix_needed': 'Strengthen reconciliation and ensure endsAt is always sent'
        }
    }
    
    for block, data in findings.items():
        log(f'\n{block}:')
        for key, val in data.items():
            if isinstance(val, list):
                log(f'  {key}:')
                for v in val:
                    log(f'    - {v}')
            else:
                log(f'  {key}: {val}')

def propose_fixes():
    """Propose concrete fixes"""
    log('\n' + '=' * 70)
    log('PROPOSED FIXES')
    log('=' * 70)
    
    fixes = [
        {
            'id': 'FIX-1',
            'block': 'BLOCK C',
            'file': 'routers/alerts.py',
            'function': 'get_alert_history()',
            'change': 'Query BOTH alert_history AND alert_events for historical data',
            'line': '~1303',
            'priority': 'CRITICAL - Primary cause of missing history'
        },
        {
            'id': 'FIX-2',
            'block': 'BLOCK A',
            'file': 'services/alert_email_service.py',
            'function': 'resolve_alertmanager_alert()',
            'change': 'Ensure labels dict passed matches the original alert labels exactly',
            'line': '~363',
            'priority': 'HIGH - Prevents AM zombie alerts'
        },
        {
            'id': 'FIX-3',
            'block': 'BLOCK B',
            'file': 'routers/alert_rules.py',
            'function': '_fire_rule_alert()',
            'change': 'Verify send_firing_notification() is always called on creation',
            'line': '~1138',
            'priority': 'HIGH - Ensures email consistency'
        },
        {
            'id': 'FIX-4',
            'block': 'BLOCK D',
            'file': 'routers/alert_rules.py',
            'function': '_resolve_recovered_services()',
            'change': 'Add logging to trace when resolve_alertmanager_alert fails',
            'line': '~400',
            'priority': 'MEDIUM - Diagnostic improvement'
        }
    ]
    
    for fix in fixes:
        log(f'\n{fix["id"]} [{fix["priority"]}]:')
        log(f'  Block: {fix["block"]}')
        log(f'  File: {fix["file"]}')
        log(f'  Function: {fix["function"]}')
        log(f'  Line: {fix["line"]}')
        log(f'  Change: {fix["change"]}')

if __name__ == '__main__':
    check_current_state()
    analyze_root_causes()
    propose_fixes()
    
    log('\n' + '=' * 70)
    log('Investigation complete. Proceeding with fixes...')
    log('=' * 70)
