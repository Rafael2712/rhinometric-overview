# APM Demo Trace Generator

Generates realistic multi-service OpenTelemetry traces for APM validation in
the Rhinometric console.

## Services Simulated

| Service | Description |
|---|---|
| `demo-ecommerce-api` | API Gateway — entry point for all requests |
| `demo-order-service` | Order processing with DB operations |
| `demo-payment-service` | Payment gateway integration |
| `demo-inventory-service` | Stock level checks with DB queries |
| `demo-notification-service` | Email / push / SMS fan-out |

## Trace Scenarios

| Scenario | Spans | Pattern |
|---|---|---|
| Successful order | 9 | API → Order → Inventory → Payment → Notification |
| Product search | 3 | API → Inventory (DB query) |
| Slow inventory | 3 | API → Inventory (800ms–2s DB query) |
| Payment error | 7 | API → Order → Payment [ERROR 502] → Rollback |
| Bulk notification | 4 | Notification → email + push + SMS |

## How It Works

- Runs inside the `rhinometric-console-backend` container (uses its OTel SDK)
- Exports to `rhinometric-otel-collector:4317` via gRPC
- Initial burst of 8 traces, then 1 trace every 8–15 seconds
- Managed by a systemd unit for auto-restart

## Installation

```bash
# Copy script to config directory
cp apm_demo_generator.py /opt/rhinometric/config/

# Install systemd service
cp apm-demo-generator.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now apm-demo-generator
```

## Management

```bash
systemctl status apm-demo-generator   # Check status
journalctl -u apm-demo-generator -f   # Follow logs
systemctl stop apm-demo-generator     # Stop
systemctl start apm-demo-generator    # Start
```
