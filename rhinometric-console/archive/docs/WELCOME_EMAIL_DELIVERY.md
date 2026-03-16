# Welcome Email Delivery Modes (SMTP vs Manual)

## Overview

When a new user is created in Rhinometric, the system attempts to send a **welcome email** containing the user's credentials. If the email cannot be delivered (e.g. SMTP ports are blocked), the system falls back to a **manual delivery mode** — the admin is shown the credentials in the UI for one-time secure copying.

## Delivery Modes

| Mode     | Trigger                          | Admin UX                                         |
|----------|----------------------------------|--------------------------------------------------|
| `email`  | SMTP connection succeeds         | Green banner: "Welcome email sent to user@x.com" |
| `manual` | SMTP timeout / config missing    | Amber banner: "SMTP unavailable — copy creds now" + Copy button |

## Required Outbound Ports

| Service   | Host             | Port | Protocol      |
|-----------|------------------|------|---------------|
| Zoho SMTP | smtp.zoho.eu     | 587  | STARTTLS/TCP  |
| Zoho SMTP | smtp.zoho.eu     | 465  | SSL/TLS/TCP   |

> **On-prem note:** If your network/firewall blocks outbound TCP 587 and 465, the system will operate in `manual` mode. User creation is **never blocked** by SMTP failures.

## SMTP Configuration

SMTP settings are managed in **Settings → Notification Channels → Email** (stored in `notification_channels.json`):

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.zoho.eu",
    "smtp_port": 587,
    "smtp_username": "user@rhinometric.com",
    "smtp_password": "***",
    "smtp_require_tls": true,
    "from_email": "user@rhinometric.com",
    "to_emails": ["alerts@example.com"]
  }
}
```

## API Response

`POST /api/users/` now returns these additional fields:

```json
{
  "id": 5,
  "username": "jdoe",
  "email": "jdoe@example.com",
  "welcome_email_sent": false,
  "delivery_mode": "manual",
  "temporary_password": "Temp1234!"
}
```

- `welcome_email_sent` — `true` if the email was delivered, `false` otherwise.
- `delivery_mode` — `"email"` or `"manual"`.
- `temporary_password` — The plain-text password, returned **only once**, only when `must_change_password=true` AND email was not sent. Never stored or logged.

## What the User Sees

### If SMTP works (delivery_mode = "email")

The admin sees a green confirmation:

> ✅ **Welcome email sent**
> Credentials were sent to jdoe@example.com.
> The user must change their password on first login.

### If SMTP is blocked (delivery_mode = "manual")

The admin sees an amber warning with a credentials box:

> ⚠️ **SMTP unavailable — copy credentials now**
>
> The welcome email could not be sent. Please copy the credentials
> below and share them securely with the user.
> **This is the only time the password will be shown.**
>
> ```
> Username: jdoe
> Email:    jdoe@example.com
> Password: Temp1234!
> ```
>
> [📋 Copy credentials]

## Observability

- **Structured log on failure:**
  `WELCOME_EMAIL_FAILED: smtp timeout — host=smtp.zoho.eu port=587 target=jdoe@example.com user=jdoe`
- **Audit event:** `welcome_email_delivery` with `delivery_mode=email|manual` in metadata.

## Troubleshooting

1. **Test SMTP connectivity from the VM:**
   ```bash
   nc -vz smtp.zoho.eu 587   # Should respond immediately if port is open
   ```

2. **Check backend logs:**
   ```bash
   docker logs rhinometric-console-backend --tail 50 | grep WELCOME_EMAIL
   ```

3. **Verify notification channels config:**
   ```bash
   docker exec rhinometric-console-backend cat /app/data/notification_channels.json
   ```
