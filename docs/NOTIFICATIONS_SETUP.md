# Rhinometric - Notifications Setup Guide

Complete guide for configuring Slack and Email notifications in Rhinometric Console.

## Overview

Rhinometric sends two types of alerts:

| Type | Source | Controlled by Settings Toggle |
|------|--------|-------------------------------|
| **AI Anomaly Alerts** | AI Anomaly Detection Engine | Yes — "AI Alerting" toggle |
| **Prometheus Alerts** | Prometheus alerting rules | No — always active if channels configured |

The **Notification Channels** section in Settings controls *where* notifications go (Slack / Email).
The **AI Alerting** toggle controls *whether* AI anomalies generate external notifications.

---

## Step 1: Open Settings

Navigate to **Settings** in the left sidebar of the Rhinometric Console (requires Admin or Owner role).

---

## Step 2: Configure Slack

### Prerequisites
- A Slack workspace where you have permission to add apps/webhooks
- An Incoming Webhook URL

### Create a Slack Webhook
1. Go to [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks)
2. Click **"Create your Slack app"** → **From scratch**
3. Name it `Rhinometric Alerts`, select your workspace
4. Go to **Incoming Webhooks** → Toggle **On**
5. Click **"Add New Webhook to Workspace"**
6. Choose the channel (e.g., `#rhinometric-alerts`)
7. Copy the **Webhook URL** (starts with `https://hooks.slack.com/services/...`)

### Configure in Rhinometric
1. In Settings → Notification Channels → **Slack**: toggle **On**
2. Paste the Webhook URL
3. Optionally change the channel (usually determined by the webhook)
4. Click **"Send Test Message"** to verify
5. Click **"Save Notification Channels"**

### Troubleshooting Slack
| Issue | Solution |
|-------|----------|
| `channel_not_found` | The channel doesn't exist or webhook doesn't have access |
| `invalid_payload` | Check webhook URL format (must start with `https://hooks.slack.com/`) |
| Timeout | Check network/firewall allows outbound HTTPS to `hooks.slack.com` |
| No message received | Verify the channel matches your webhook configuration |

---

## Step 3: Configure Email (SMTP)

### Prerequisites
- An SMTP server (e.g., Zoho Mail, Gmail, Amazon SES, custom SMTP)
- SMTP credentials (username + password or app password)

### SMTP Settings for Common Providers

| Provider | Host | Port | TLS | Notes |
|----------|------|------|-----|-------|
| **Zoho Mail** | `smtp.zoho.eu` (EU) / `smtp.zoho.com` (US) | 587 | STARTTLS | Use app-specific password if 2FA enabled |
| **Gmail** | `smtp.gmail.com` | 587 | STARTTLS | Requires App Password (not regular password) |
| **Amazon SES** | `email-smtp.{region}.amazonaws.com` | 587 | STARTTLS | Use SES SMTP credentials (not IAM) |
| **Office 365** | `smtp.office365.com` | 587 | STARTTLS | May require admin approval |
| **Custom** | Your SMTP host | Usually 587 or 465 | Varies | Check with your provider |

### Zoho Mail Specific Setup
1. Log in to [accounts.zoho.com](https://accounts.zoho.com)
2. Go to **Security** → **App Passwords**
3. Generate a new app password for "Rhinometric"
4. Use this password (not your regular login password) in the SMTP Password field

### Configure in Rhinometric
1. In Settings → Notification Channels → **Email (SMTP)**: toggle **On**
2. Fill in:
   - **SMTP Host**: e.g., `smtp.zoho.eu`
   - **Port**: `587` (standard STARTTLS)
   - **Username**: your SMTP login (usually your email)
   - **Password**: SMTP password or app password
   - **From Email**: sender address (usually same as username)
   - **To Email(s)**: comma-separated list of recipients
3. Enable **Require STARTTLS** (recommended for port 587)
4. Click **"Send Test Email"** to verify
5. Click **"Save Notification Channels"**

### Troubleshooting Email
| Issue | Solution |
|-------|----------|
| `SMTP authentication failed` | Check username/password. For Zoho/Gmail, use app-specific password. |
| `Connection timed out` | Verify host:port is correct. Check firewall allows outbound on port 587. |
| `TLS handshake failed` | Try toggling STARTTLS. Port 465 uses implicit SSL (untoggle STARTTLS). |
| `Sender address rejected` | "From Email" must be authorized in your SMTP provider. |
| Email goes to spam | Add SPF/DKIM records for your domain. Use a verified sender. |

---

## Step 4: Enable AI Alerting

Once channels are configured:

1. In Settings, toggle **"Enable AI Alerting"** to **On**
2. Only **critical** severity AI anomalies will send notifications
3. Lower severities (high, medium, low) remain visible only in the console

### What gets notified?

| Severity | Console UI | Slack/Email |
|----------|-----------|-------------|
| Critical | ✅ Always | ✅ When AI Alerting ON |
| High | ✅ Always | ❌ Never |
| Medium | ✅ Always | ❌ Never |
| Low | ✅ Always | ❌ Never |

---

## Architecture Notes

### Defense in Depth
The AI alerting toggle uses two independent gates:

1. **Source Gate**: The AI engine itself stops sending alerts to Alertmanager when disabled
2. **Routing Gate**: Alertmanager routes AI alerts to a "blackhole" receiver when disabled

Both must fail for a false notification to occur.

### Data Storage
- Settings: `/app/data/settings.json` (volume-mounted, survives restarts)
- Channels: `/app/data/notification_channels.json` (volume-mounted, chmod 600, secrets at rest)
- No secrets are ever committed to git

### Alertmanager Integration
When you save notification channels, Rhinometric:
1. Regenerates `alertmanager.yml` from a structured template
2. Reloads Alertmanager via `/-/reload` API call
3. All routes and receivers are updated atomically

---

## FAQ

**Q: Do Prometheus generic alerts use the same channels?**
A: Yes. All standard alerting (critical/warning/info) uses the Slack and Email channels you configure. The AI Alerting toggle only controls AI anomaly alerts.

**Q: What happens if I disable both Slack and Email?**
A: No external notifications will be sent. Alerts still appear in the console UI and can be viewed in the Alerts page.

**Q: Are my SMTP credentials secure?**
A: Credentials are stored in `/app/data/notification_channels.json` with file permissions `600` (owner-only read/write). They are never exposed via the API (passwords are redacted in GET responses).

**Q: Can I change notification channels without restarting?**
A: Yes. Saving channels instantly regenerates the Alertmanager config and triggers a hot reload. No container restart needed.
