# Rhinometric Console — Notifications Setup Guide

> **Version:** 2.5.1 | **Time to configure:** ~10 minutes  
> **Applies to:** Rhinometric Console (Settings → Notification Channels)

---

## Table of Contents

1. [What Are Notification Channels?](#what-are-notification-channels)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Enable AI Anomaly Alerting](#step-1--enable-ai-anomaly-alerting)
4. [Step 2 — Configure Slack](#step-2--configure-slack)
5. [Step 3 — Configure Email](#step-3--configure-email)
6. [Step 4 — Send Test Messages](#step-4--send-test-messages)
7. [Step 5 — Validate End-to-End](#step-5--validate-end-to-end)
8. [How Alerts Work](#how-alerts-work)
9. [FAQ](#faq)
10. [Quick Verification Checklist](#quick-verification-checklist)

---

## What Are Notification Channels?

Notification Channels let Rhinometric Console send **real-time alerts** when the AI anomaly detection engine finds something unusual in your infrastructure. You can receive alerts through:

| Channel | What You Get |
|---------|-------------|
| **Slack** | Instant message in a Slack channel with anomaly details and action buttons |
| **Email** | HTML email with full anomaly breakdown and links to dashboards |

Each alert includes:
- Metric name, severity, and deviation percentage
- Current value vs expected baseline
- **"Ver Dashboard en Consola"** button — opens the relevant dashboard inside the Console
- **"Ver en Grafana"** button — opens the specific Grafana panel for that metric

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Console access** | Admin or Owner role required |
| **Slack** | A Slack workspace where you can create Incoming Webhooks |
| **Email** | A mail service (Zoho Mail, Gmail, etc.) with API or SMTP access |

---

## Step 1 — Enable AI Anomaly Alerting

1. Log in to **Rhinometric Console** with an **Admin** account
2. Click **⚙️ Settings** in the left sidebar
3. In the **AI Anomaly Alerting** section, make sure the toggle is **ON** (green)
4. Click **Save**

> **What this does:** When ON, critical anomalies detected by the AI engine trigger notifications through your configured channels. When OFF, anomalies are still detected and visible in the AI Anomalies page, but no Slack/email alerts are sent.

**Expected result:** Green confirmation banner: *"AI alerting settings saved"*

---

## Step 2 — Configure Slack

### 2.1 Create an Incoming Webhook in Slack

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → select **"From scratch"**
3. Enter a name (e.g., `Rhinometric Alerts`) and choose your workspace
4. In the left menu, click **"Incoming Webhooks"**
5. Toggle **"Activate Incoming Webhooks"** to ON
6. Click **"Add New Webhook to Workspace"**
7. Select the **channel** where you want to receive alerts (e.g., `#alerts`)
8. Click **"Allow"**
9. **Copy the Webhook URL** — it looks like: `https://hooks.slack.com/services/TXXXXX/BXXXXX/xxxxxxxx`

### 2.2 Configure in Rhinometric Console

1. Go to **Settings** → scroll to **Notification Channels** → **Slack** section
2. Fill in the fields:

| Field | What to Enter |
|-------|--------------|
| **Enabled** | Toggle **ON** |
| **Webhook URL** | Paste the URL you copied from Slack |
| **Channel** | The channel name with `#` prefix (e.g., `#alerts`) |

3. Click **💾 Save Channels**

**Expected result:** Green banner: *"Notification channels saved and Alertmanager reloaded"*

### 2.3 What Slack Alerts Look Like

When a critical anomaly fires, you receive a Slack message like:

```
🔴 [CRITICAL] AI Anomaly: node_cpu_usage

Desviacion: 104.6% respecto al baseline
Valor actual: 92.5 | Baseline esperado: 45.2

Contexto:
• Componente: node-exporter
• Metrica: node_cpu_usage
• Severidad: CRITICAL
• Estado: firing

🖥️ Ver Dashboard en Consola
📈 Ver CPU en Grafana

[Ver Dashboard en Consola]  [Ver en Grafana]
```

**What if it fails?** See [FAQ](#faq) below.

---

## Step 3 — Configure Email

### 3.1 Fill in Email Settings

1. Go to **Settings** → scroll to **Notification Channels** → **Email** section
2. Fill in the fields:

| Field | What to Enter | Example |
|-------|--------------|---------|
| **Enabled** | Toggle **ON** | ✅ |
| **SMTP Host** | Your mail server hostname | `smtp.zoho.eu` or `smtp.gmail.com` |
| **SMTP Port** | Usually 587 (TLS) or 465 (SSL) | `587` |
| **SMTP Username** | Your email login | `alerts@yourcompany.com` |
| **SMTP Password** | App password or mail password | `••••••••` |
| **Use TLS** | Keep ON for port 587 | ✅ |
| **From Email** | Sender address (must be verified) | `alerts@yourcompany.com` |
| **To Emails** | Recipients, comma-separated | `admin@yourcompany.com, ops@yourcompany.com` |

3. Click **💾 Save Channels**

**Expected result:** Green banner: *"Notification channels saved and Alertmanager reloaded"*

### 3.2 SMTP Ports Blocked? (Hetzner, some cloud providers)

Some hosting providers block outbound SMTP ports (25, 465, 587). If you see timeout errors when testing email, the platform has a **built-in fallback**: it can send emails via the **Zoho Mail REST API** over HTTPS (port 443), which is never blocked.

To enable this fallback, your system administrator needs to configure Zoho API credentials on the server. See the [Technical Documentation](NOTIFICATIONS_TECH.md) for setup details.

### 3.3 What Email Alerts Look Like

You receive an HTML email with:
- **Red header** (critical) or **orange header** (warning) showing the anomaly name
- Metric details: name, severity, component, service, current/expected values
- Two buttons:
  - 🔵 **"Ver Dashboard en Consola"** — opens the matching dashboard inside the Console app
  - 🟡 **"Ver en Grafana"** — opens the specific Grafana panel for that metric

---

## Step 4 — Send Test Messages

### Test Slack

1. In **Settings → Notification Channels → Slack**
2. Click the **"🚀 Send Test Message"** button
3. Check your Slack channel for a test message

| Result | Meaning |
|--------|---------|
| ✅ *"Slack test message sent successfully"* | Webhook is valid and channel is reachable |
| ❌ Error with HTTP code | Check webhook URL, channel name, and that the Slack app is installed |

### Test Email

1. In **Settings → Notification Channels → Email**
2. Click the **"🚀 Send Test Email"** button
3. Check your inbox (and spam folder)

| Result | Meaning |
|--------|---------|
| ✅ *"Test email sent successfully"* | Mail delivery works |
| ❌ Timeout error | SMTP ports may be blocked — ask admin about Zoho API fallback |
| ❌ Authentication error | Check username/password and "Allow less secure apps" if using Gmail |

---

## Step 5 — Validate End-to-End

After configuring both channels, confirm that **real** AI anomaly alerts will work:

1. **Verify AI Alerting is ON** — Settings → AI Anomaly Alerting toggle should be green
2. **Check the AI Anomalies page** — Navigate to **AI Anomalies** in the sidebar. If you see active anomalies with severity **CRITICAL**, those should trigger alerts
3. **Wait for a real anomaly** or ask your administrator to fire a test alert through Alertmanager
4. **Confirm delivery:**
   - Slack: check the configured channel
   - Email: check the configured recipients' inboxes
5. **Click the buttons** in the alert to verify they open the correct dashboard

> **Note:** Only **CRITICAL** severity anomalies trigger Slack and email alerts by default. Lower severities (WARNING, MEDIUM, LOW) appear in the AI Anomalies page but don't send notifications.

---

## How Alerts Work

```
AI Engine detects anomaly → Prometheus alert rule fires
                                    ↓
                           Alertmanager receives alert
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓                               ↓
             Slack Webhook                  Email Webhook
                    ↓                               ↓
         Message in #channel            HTML email to recipients
         with action buttons            with action buttons
```

### Which Dashboard Do the Buttons Open?

| Metric Type | Console Dashboard | Grafana Panel |
|-------------|------------------|---------------|
| CPU (`node_cpu_usage`) | System Overview | CPU gauge (Panel 1) |
| Memory (`node_memory_usage`) | System Overview | Memory gauge (Panel 2) |
| Disk (`node_disk_usage`, `node_disk_io`) | System Overview | Disk gauge (Panel 3) |
| Network (`node_network_*`) | System Overview | Network Traffic (Panel 6) |
| Website/SSL/Other metrics | AI Anomaly Service | Full anomaly dashboard |

---

## FAQ

### Why am I not receiving alerts?

1. Check that **AI Anomaly Alerting** is **ON** in Settings
2. Check that Slack and/or Email channels are **Enabled**
3. Use the **Test** buttons to verify connectivity
4. Only **CRITICAL** anomalies trigger alerts — check the AI Anomalies page for active critical anomalies
5. If tests work but real alerts don't arrive, the alert routing may need review — contact your admin

### Can I send alerts to multiple Slack channels?

Currently, alerts go to **one Slack channel**. To forward to multiple channels, set up a Slack workflow or automation.

### Can I add more email recipients?

Yes. In the **To Emails** field, separate addresses with commas:
```
admin@company.com, devops@company.com, oncall@company.com
```

### What happens if Slack or email fails?

- If Slack fails, email still sends (and vice versa)
- Anomaly detection **never stops** due to notification failures
- Errors appear in backend logs for your admin to diagnose

### How do I change the Slack channel?

1. Create a new Incoming Webhook for the new channel (in Slack settings)
2. In Console Settings, update **Webhook URL** and **Channel**
3. Click **Save Channels** and test

### Are my credentials secure?

- Credentials are stored server-side in a file with restricted permissions (chmod 600)
- The API **never returns** full webhook URLs or SMTP passwords — they appear redacted
- Zoho API tokens are auto-refreshed and cached in memory only

---

## Quick Verification Checklist

Use this after initial setup or after any configuration change:

- [ ] **AI Alerting toggle** is ON (Settings page, green indicator)
- [ ] **Slack**: Enabled, Webhook URL filled, Channel set
- [ ] **Slack test**: "Send Test Message" succeeds and message appears in Slack
- [ ] **Email**: Enabled, all SMTP fields filled, at least one recipient in To Emails
- [ ] **Email test**: "Send Test Email" succeeds and email arrives in inbox
- [ ] **Save**: "Notification channels saved and Alertmanager reloaded" confirmation appears
- [ ] **AI Anomalies page**: Shows active anomalies (confirms detection engine is running)
- [ ] **Real alert**: Wait for or trigger a CRITICAL anomaly, verify it arrives in both channels
- [ ] **Buttons**: Click "Ver Dashboard en Consola" and "Ver en Grafana" in the alert — both open the correct dashboard
