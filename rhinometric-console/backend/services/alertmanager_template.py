#!/usr/bin/env python3
"""
Alertmanager Template Renderer for Rhinometric.

Generates alertmanager.yml from structured config instead of regex edits.
Called by settings.py when notification channels are saved.
"""

import yaml
import os
import json
import logging
import copy

logger = logging.getLogger("rhinometric.alertmanager_template")

CHANNELS_FILE = os.environ.get(
    "NOTIFICATION_CHANNELS_FILE",
    "/app/data/notification_channels.json"
)
ALERTMANAGER_CONFIG = "/etc/alertmanager/alertmanager.yml"

DEFAULT_CHANNELS = {
    "slack": {
        "enabled": False,
        "webhook_url": "",
        "channel": "#rhinometric-alerts",
    },
    "email": {
        "enabled": False,
        "smtp_host": "smtp.zoho.eu",
        "smtp_port": 587,
        "smtp_username": "",
        "smtp_password": "",
        "smtp_require_tls": True,
        "from_email": "",
        "to_emails": [],
    }
}


def load_channels() -> dict:
    """Load notification channel config from disk."""
    try:
        if os.path.exists(CHANNELS_FILE):
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load channels: {e}")
    return copy.deepcopy(DEFAULT_CHANNELS)


def save_channels(channels: dict):
    """Save notification channel config to disk (chmod 600)."""
    os.makedirs(os.path.dirname(CHANNELS_FILE), exist_ok=True)
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=2)
    try:
        os.chmod(CHANNELS_FILE, 0o600)
    except Exception:
        pass
    logger.info("Notification channels saved")


def redact_channels(channels: dict) -> dict:
    """Return channels with secrets redacted for API responses."""
    out = copy.deepcopy(channels)
    # Redact Slack webhook
    if out.get("slack", {}).get("webhook_url"):
        url = out["slack"]["webhook_url"]
        if len(url) > 20:
            out["slack"]["webhook_url"] = url[:25] + "..." + url[-6:]
        else:
            out["slack"]["webhook_url"] = "***configured***"
    # Redact SMTP password
    if out.get("email", {}).get("smtp_password"):
        out["email"]["smtp_password"] = "••••••••"
    return out


def render_alertmanager_config(channels: dict, ai_alerting_enabled: bool) -> str:
    """
    Render the full alertmanager.yml from structured config.
    
    This replaces all regex-based editing with a deterministic template.
    Preserves: routes, inhibit_rules, templates, Prometheus receivers.
    Dynamically generates: global SMTP, ai-anomaly-alerts receiver.
    """
    email_cfg = channels.get("email", {})
    slack_cfg = channels.get("slack", {})

    # --- Global section ---
    global_section = {"resolve_timeout": "5m"}

    if email_cfg.get("enabled") and email_cfg.get("smtp_host"):
        global_section["smtp_from"] = email_cfg.get("from_email", "")
        global_section["smtp_smarthost"] = f"{email_cfg['smtp_host']}:{email_cfg.get('smtp_port', 587)}"
        global_section["smtp_auth_username"] = email_cfg.get("smtp_username", "")
        global_section["smtp_auth_password"] = email_cfg.get("smtp_password", "")
        global_section["smtp_require_tls"] = email_cfg.get("smtp_require_tls", True)

    if slack_cfg.get("enabled") and slack_cfg.get("webhook_url"):
        global_section["slack_api_url"] = slack_cfg["webhook_url"]

    # --- Templates ---
    templates_section = ["/etc/alertmanager/templates/*.tmpl"]

    # --- Route section ---
    ai_critical_receiver = "ai-anomaly-alerts" if ai_alerting_enabled else "blackhole"

    route_section = {
        "receiver": "team-notifications",
        "group_by": ["alertname", "instance", "severity"],
        "group_wait": "30s",
        "group_interval": "5m",
        "repeat_interval": "4h",
        "routes": [
            {
                "match": {
                    "rhinometric_source": "ai-anomaly",
                    "severity": "critical"
                },
                "receiver": ai_critical_receiver,
                "group_by": ["alertname", "metric", "severity"],
                "group_wait": "30s",
                "group_interval": "5m",
                "repeat_interval": "4h",
                "continue": False,
            },
            {
                "match": {"rhinometric_source": "ai-anomaly"},
                "receiver": "blackhole",
                "group_by": ["alertname", "metric", "severity"],
                "group_wait": "30s",
                "group_interval": "5m",
                "repeat_interval": "4h",
                "continue": False,
            },
            {
                "match": {"severity": "critical"},
                "receiver": "critical-alerts",
                "group_wait": "10s",
                "group_interval": "1m",
                "repeat_interval": "1h",
            },
            {
                "match": {"severity": "warning"},
                "receiver": "warning-alerts",
                "repeat_interval": "6h",
            },
            {
                "match": {"severity": "info"},
                "receiver": "info-alerts",
                "repeat_interval": "24h",
            },
        ]
    }

    # --- AI Anomaly Alerts Receiver ---
    ai_anomaly_receiver = {"name": "ai-anomaly-alerts"}

    if slack_cfg.get("enabled") and slack_cfg.get("webhook_url"):
        slack_channel = slack_cfg.get("channel", "#rhinometric-alerts")
        ai_anomaly_receiver["slack_configs"] = [{
            "channel": slack_channel,
            "username": "Rhinometric AI",
            "icon_emoji": ":brain:",
            "title": '{{ template "ai_anomaly_slack_title" (index .Alerts 0) }}',
            "text": '{{ template "ai_anomaly_slack" . }}',
            "actions": [
                {
                    "type": "button",
                    "text": "Ver Dashboard en Consola",
                    "url": '{{- $m := (index .Alerts 0).Labels.metric -}}{{- if or (eq $m "node_cpu_usage") (eq $m "node_memory_usage") (eq $m "node_disk_usage") (eq $m "node_disk_io") (eq $m "node_network_receive") (eq $m "node_network_transmit") -}}https://console-staging.rhinometric.com/dashboards/rhinometric-system-overview/view{{- else -}}https://console-staging.rhinometric.com/dashboards/ai-anomaly-service/view{{- end -}}'
                },
                {
                    "type": "button",
                    "text": "Ver en Grafana",
                    "url": '{{- $m := (index .Alerts 0).Labels.metric -}}{{- if eq $m "node_cpu_usage" -}}http://46.225.231.117/grafana/d/rhinometric-system-overview/01-system-overview?viewPanel=1&theme=dark{{- else if eq $m "node_memory_usage" -}}http://46.225.231.117/grafana/d/rhinometric-system-overview/01-system-overview?viewPanel=2&theme=dark{{- else if or (eq $m "node_disk_usage") (eq $m "node_disk_io") -}}http://46.225.231.117/grafana/d/rhinometric-system-overview/01-system-overview?viewPanel=3&theme=dark{{- else if or (eq $m "node_network_receive") (eq $m "node_network_transmit") -}}http://46.225.231.117/grafana/d/rhinometric-system-overview/01-system-overview?viewPanel=6&theme=dark{{- else -}}http://46.225.231.117/grafana/d/ai-anomaly-service/05-ai-anomaly-service?theme=dark{{- end -}}'
                },
            ],
            "send_resolved": True,
        }]

    if email_cfg.get("enabled") and email_cfg.get("to_emails"):
        # Use webhook to send emails via Zoho API (SMTP ports blocked on Hetzner)
        backend_url = "http://rhinometric-console-backend:8105"
        ai_anomaly_receiver["webhook_configs"] = [{
            "url": f"{backend_url}/api/settings/alertmanager-webhook/email",
            "send_resolved": True,
        }]

    # --- Standard Receivers (team-notifications, critical, warning, info) ---
    # These use the same channels but are for Prometheus generic alerts
    def _build_standard_receiver(name, subject_tpl, slack_channel, slack_color=None):
        recv = {"name": name}
        if email_cfg.get("enabled") and email_cfg.get("to_emails"):
            to_addr = ", ".join(email_cfg["to_emails"])
            recv["email_configs"] = [{
                "to": to_addr,
                "html": '{{ template "email.html" . }}',
                "headers": {"Subject": subject_tpl}
            }]
        if slack_cfg.get("enabled") and slack_cfg.get("webhook_url"):
            sc = {
                "channel": slack_channel,
                "title": f'{{{{ .GroupLabels.alertname }}}}',
                "text": '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}',
            }
            if slack_color:
                sc["color"] = slack_color
            recv["slack_configs"] = [sc]
        return recv

    team_recv = _build_standard_receiver(
        "team-notifications",
        "Rhinometric Alert: {{ .GroupLabels.alertname }}",
        "#rhinometric-alerts"
    )

    critical_recv = _build_standard_receiver(
        "critical-alerts",
        "[CRITICAL] {{ .GroupLabels.alertname }}",
        "#rhinometric-critical",
        "danger"
    )
    # Add priority header to critical emails
    if "email_configs" in critical_recv:
        critical_recv["email_configs"][0]["headers"]["Priority"] = "urgent"

    warning_recv = _build_standard_receiver(
        "warning-alerts",
        "[WARNING] {{ .GroupLabels.alertname }}",
        "#rhinometric-alerts",
        "warning"
    )

    info_recv = _build_standard_receiver(
        "info-alerts",
        "[INFO] {{ .GroupLabels.alertname }}",
        "#rhinometric-info",
        "#439FE0"
    )

    blackhole_recv = {"name": "blackhole"}

    receivers = [
        ai_anomaly_receiver,
        team_recv,
        critical_recv,
        warning_recv,
        info_recv,
        blackhole_recv,
    ]

    # --- Inhibit Rules ---
    inhibit_rules = [
        {"source_match": {"severity": "critical"}, "target_match": {"severity": "warning"}, "equal": ["alertname", "instance"]},
        {"source_match": {"severity": "critical"}, "target_match": {"severity": "info"}, "equal": ["alertname", "instance"]},
        {"source_match": {"severity": "warning"}, "target_match": {"severity": "info"}, "equal": ["alertname", "instance"]},
    ]

    # --- Assemble ---
    config = {
        "global": global_section,
        "templates": templates_section,
        "route": route_section,
        "receivers": receivers,
        "inhibit_rules": inhibit_rules,
    }

    # Custom YAML representer to handle Go template strings properly
    class AlertmanagerDumper(yaml.SafeDumper):
        pass

    def str_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        if any(c in data for c in '{}[]%#&*!|>\'\"@`'):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    AlertmanagerDumper.add_representer(str, str_representer)

    return yaml.dump(config, Dumper=AlertmanagerDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)


def write_alertmanager_config(channels: dict, ai_alerting_enabled: bool) -> bool:
    """Render and write alertmanager.yml. Returns True on success."""
    try:
        content = render_alertmanager_config(channels, ai_alerting_enabled)
        with open(ALERTMANAGER_CONFIG, "w") as f:
            f.write(content)
        logger.info("Alertmanager config written from template")
        return True
    except Exception as e:
        logger.error(f"Failed to write alertmanager config: {e}")
        return False
