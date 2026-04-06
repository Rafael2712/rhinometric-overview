#!/usr/bin/env python3
"""
APM Demo Trace Generator — Rhinometric
Generates realistic multi-service traces for APM validation.
Runs inside rhinometric-console-backend container (OTel SDK available).
"""

import time
import random
import logging
from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import StatusCode, SpanKind

logging.basicConfig(level=logging.INFO, format="%(asctime)s [APM-DEMO] %(message)s")
log = logging.getLogger("apm-demo")

OTEL_ENDPOINT = "rhinometric-otel-collector:4317"

# ---------------------------------------------------------------------------
# Service definitions — names that pass the internal-service filter
# ---------------------------------------------------------------------------
SERVICES = {
    "demo-ecommerce-api": "API Gateway for the e-commerce platform",
    "demo-order-service": "Processes and manages customer orders",
    "demo-payment-service": "Handles payment transactions",
    "demo-inventory-service": "Manages product inventory and stock levels",
    "demo-notification-service": "Sends email and push notifications",
}

# Create a TracerProvider + Tracer per service
tracers: dict[str, trace.Tracer] = {}
providers: list[TracerProvider] = []

for svc_name, description in SERVICES.items():
    resource = Resource.create({
        SERVICE_NAME: svc_name,
        "service.version": "1.4.0",
        "deployment.environment": "demo",
    })
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(
        exporter,
        max_queue_size=512,
        schedule_delay_millis=500,
        max_export_batch_size=64,
    ))
    providers.append(provider)
    tracers[svc_name] = provider.get_tracer(svc_name, "1.4.0")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PRODUCTS = [
    ("SKU-1001", "Wireless Headphones", 79.99),
    ("SKU-1002", "USB-C Hub", 49.99),
    ("SKU-1003", "Mechanical Keyboard", 129.99),
    ("SKU-1004", "4K Monitor", 399.99),
    ("SKU-1005", "Laptop Stand", 34.99),
]

CUSTOMERS = ["cust-alice", "cust-bob", "cust-charlie", "cust-diana", "cust-evan"]
PAYMENT_METHODS = ["credit_card", "paypal", "apple_pay", "crypto"]
HTTP_METHODS = ["GET", "POST", "PUT"]
USER_AGENTS = [
    "Mozilla/5.0 Chrome/120",
    "Mozilla/5.0 Firefox/121",
    "RhinoMetric-SDK/2.1",
]

def _sleep_jitter(base_ms: float, jitter_ms: float = 0):
    """Simulate work with realistic timing."""
    total = base_ms + random.uniform(0, jitter_ms)
    time.sleep(total / 1000.0)


def _set_http_attrs(span, method="GET", route="/", status=200):
    span.set_attribute("http.method", method)
    span.set_attribute("http.route", route)
    span.set_attribute("http.status_code", status)
    span.set_attribute("http.user_agent", random.choice(USER_AGENTS))


# ---------------------------------------------------------------------------
# Trace Scenarios
# ---------------------------------------------------------------------------

def scenario_successful_order():
    """Normal order flow: API → Order → Inventory(check) → Payment → Notification."""
    customer = random.choice(CUSTOMERS)
    product = random.choice(PRODUCTS)
    sku, name, price = product
    order_id = f"ORD-{random.randint(10000, 99999)}"

    api = tracers["demo-ecommerce-api"]
    with api.start_as_current_span("POST /api/orders", kind=SpanKind.SERVER) as root:
        _set_http_attrs(root, "POST", "/api/orders", 201)
        root.set_attribute("customer.id", customer)
        root.set_attribute("order.id", order_id)

        # Validate request
        with api.start_as_current_span("validate_request") as val_span:
            val_span.set_attribute("validation.fields", 5)
            _sleep_jitter(2, 3)

        # Order service: create order
        order_tracer = tracers["demo-order-service"]
        with order_tracer.start_as_current_span("create_order", kind=SpanKind.INTERNAL) as order_span:
            order_span.set_attribute("order.id", order_id)
            order_span.set_attribute("order.product_sku", sku)
            order_span.set_attribute("order.product_name", name)
            order_span.set_attribute("order.amount", price)

            # DB insert
            with order_tracer.start_as_current_span("INSERT orders") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", f"INSERT INTO orders (id, customer, sku, amount) VALUES ('{order_id}', '{customer}', '{sku}', {price})")
                db_span.set_attribute("db.name", "ecommerce_db")
                _sleep_jitter(5, 8)

            # Check inventory
            inv_tracer = tracers["demo-inventory-service"]
            with inv_tracer.start_as_current_span("check_stock", kind=SpanKind.CLIENT) as inv_span:
                inv_span.set_attribute("inventory.sku", sku)
                inv_span.set_attribute("inventory.available", True)
                inv_span.set_attribute("inventory.quantity", random.randint(10, 500))

                with inv_tracer.start_as_current_span("SELECT inventory") as db2:
                    db2.set_attribute("db.system", "postgresql")
                    db2.set_attribute("db.statement", f"SELECT quantity FROM inventory WHERE sku = '{sku}'")
                    _sleep_jitter(3, 5)

            # Process payment
            pay_tracer = tracers["demo-payment-service"]
            method = random.choice(PAYMENT_METHODS)
            with pay_tracer.start_as_current_span("process_payment", kind=SpanKind.CLIENT) as pay_span:
                pay_span.set_attribute("payment.method", method)
                pay_span.set_attribute("payment.amount", price)
                pay_span.set_attribute("payment.currency", "USD")
                pay_span.set_attribute("payment.status", "approved")

                # External gateway call
                with pay_tracer.start_as_current_span(f"POST https://gateway.payments.io/charge", kind=SpanKind.CLIENT) as gw:
                    gw.set_attribute("http.method", "POST")
                    gw.set_attribute("http.url", "https://gateway.payments.io/charge")
                    gw.set_attribute("http.status_code", 200)
                    _sleep_jitter(30, 50)

        # Send notification
        notif = tracers["demo-notification-service"]
        with notif.start_as_current_span("send_order_confirmation", kind=SpanKind.INTERNAL) as n:
            n.set_attribute("notification.type", "email")
            n.set_attribute("notification.recipient", f"{customer}@example.com")
            n.set_attribute("notification.template", "order_confirmation")
            _sleep_jitter(8, 12)

        root.set_attribute("http.status_code", 201)
        _sleep_jitter(1, 2)

    log.info(f"[OK] Order {order_id}: {name} (${price}) for {customer}")


def scenario_slow_inventory_check():
    """Slow request: inventory service DB query is slow."""
    sku, name, price = random.choice(PRODUCTS)

    api = tracers["demo-ecommerce-api"]
    with api.start_as_current_span("GET /api/products/{sku}/availability", kind=SpanKind.SERVER) as root:
        _set_http_attrs(root, "GET", f"/api/products/{sku}/availability", 200)
        root.set_attribute("product.sku", sku)

        inv = tracers["demo-inventory-service"]
        with inv.start_as_current_span("check_availability", kind=SpanKind.CLIENT) as inv_span:
            inv_span.set_attribute("inventory.sku", sku)

            # Slow DB query — simulates full table scan
            with inv.start_as_current_span("SELECT inventory (slow)") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", f"SELECT * FROM inventory WHERE sku = '{sku}' AND warehouse_id IN (SELECT id FROM warehouses WHERE active = true)")
                db_span.set_attribute("db.name", "ecommerce_db")
                _sleep_jitter(800, 1200)  # 800ms-2s — clearly slow
                db_span.add_event("slow_query_detected", {"query_time_ms": 1200})

            inv_span.set_attribute("inventory.available", True)
            inv_span.set_attribute("inventory.quantity", random.randint(1, 5))

        _sleep_jitter(2, 3)

    log.info(f"[SLOW] Inventory check for {sku} ({name})")


def scenario_payment_error():
    """Error trace: payment gateway returns 502."""
    customer = random.choice(CUSTOMERS)
    sku, name, price = random.choice(PRODUCTS)
    order_id = f"ORD-{random.randint(10000, 99999)}"

    api = tracers["demo-ecommerce-api"]
    with api.start_as_current_span("POST /api/orders", kind=SpanKind.SERVER) as root:
        _set_http_attrs(root, "POST", "/api/orders", 502)
        root.set_attribute("customer.id", customer)
        root.set_attribute("order.id", order_id)

        order_tracer = tracers["demo-order-service"]
        with order_tracer.start_as_current_span("create_order", kind=SpanKind.INTERNAL) as order_span:
            order_span.set_attribute("order.id", order_id)

            with order_tracer.start_as_current_span("INSERT orders") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.name", "ecommerce_db")
                _sleep_jitter(4, 6)

            # Payment fails
            pay = tracers["demo-payment-service"]
            with pay.start_as_current_span("process_payment", kind=SpanKind.CLIENT) as pay_span:
                pay_span.set_attribute("payment.method", "credit_card")
                pay_span.set_attribute("payment.amount", price)

                with pay.start_as_current_span("POST https://gateway.payments.io/charge", kind=SpanKind.CLIENT) as gw:
                    gw.set_attribute("http.method", "POST")
                    gw.set_attribute("http.url", "https://gateway.payments.io/charge")
                    gw.set_attribute("http.status_code", 502)
                    _sleep_jitter(2000, 1000)  # Long timeout before error
                    gw.set_status(StatusCode.ERROR, "Payment gateway returned 502 Bad Gateway")
                    gw.record_exception(Exception("PaymentGatewayError: 502 Bad Gateway — upstream timeout"))

                pay_span.set_status(StatusCode.ERROR, "Payment failed")
                pay_span.set_attribute("payment.status", "failed")

            # Rollback order
            with order_tracer.start_as_current_span("rollback_order") as rb:
                rb.set_attribute("order.id", order_id)
                rb.set_attribute("rollback.reason", "payment_failed")
                with order_tracer.start_as_current_span("UPDATE orders SET status='cancelled'") as db2:
                    db2.set_attribute("db.system", "postgresql")
                    _sleep_jitter(3, 5)

        root.set_status(StatusCode.ERROR, "Order failed: payment error")
        root.set_attribute("error", True)
        _sleep_jitter(1, 2)

    log.info(f"[ERR] Payment error for order {order_id}")


def scenario_product_search():
    """Simple read-only flow: API → Inventory (DB search)."""
    query = random.choice(["headphones", "keyboard", "monitor", "hub", "stand"])

    api = tracers["demo-ecommerce-api"]
    with api.start_as_current_span("GET /api/products/search", kind=SpanKind.SERVER) as root:
        _set_http_attrs(root, "GET", "/api/products/search", 200)
        root.set_attribute("search.query", query)
        root.set_attribute("search.results_count", random.randint(2, 15))

        inv = tracers["demo-inventory-service"]
        with inv.start_as_current_span("search_products", kind=SpanKind.CLIENT) as search_span:
            search_span.set_attribute("search.query", query)

            with inv.start_as_current_span("SELECT products") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", f"SELECT * FROM products WHERE name ILIKE '%{query}%' ORDER BY relevance DESC LIMIT 20")
                db_span.set_attribute("db.name", "ecommerce_db")
                _sleep_jitter(8, 15)

        _sleep_jitter(1, 2)

    log.info(f"[OK] Product search: '{query}'")


def scenario_bulk_notification():
    """Notification service sends to multiple channels — parallel-looking child spans."""
    customer = random.choice(CUSTOMERS)
    order_id = f"ORD-{random.randint(10000, 99999)}"

    notif = tracers["demo-notification-service"]
    with notif.start_as_current_span("send_notifications", kind=SpanKind.INTERNAL) as root:
        root.set_attribute("notification.order_id", order_id)
        root.set_attribute("notification.channels", 3)

        with notif.start_as_current_span("send_email") as email:
            email.set_attribute("notification.type", "email")
            email.set_attribute("notification.recipient", f"{customer}@example.com")
            _sleep_jitter(15, 20)

        with notif.start_as_current_span("send_push") as push:
            push.set_attribute("notification.type", "push")
            push.set_attribute("notification.device_token", "FCM:xxxx")
            _sleep_jitter(10, 15)

        with notif.start_as_current_span("send_sms") as sms:
            sms.set_attribute("notification.type", "sms")
            sms.set_attribute("notification.phone", "+1-555-xxxx")
            _sleep_jitter(25, 30)
            # SMS occasionally fails
            if random.random() < 0.3:
                sms.set_status(StatusCode.ERROR, "SMS provider timeout")
                sms.record_exception(Exception("SMSProviderError: Twilio timeout after 5000ms"))

    log.info(f"[OK] Bulk notification for {order_id}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
SCENARIOS = [
    (scenario_successful_order, 35),     # 35% — most common
    (scenario_product_search, 25),       # 25% — reads
    (scenario_slow_inventory_check, 15), # 15% — slow queries
    (scenario_payment_error, 10),        # 10% — errors
    (scenario_bulk_notification, 15),    # 15% — notification fan-out
]


def weighted_choice():
    total = sum(w for _, w in SCENARIOS)
    r = random.randint(1, total)
    cumulative = 0
    for fn, w in SCENARIOS:
        cumulative += w
        if r <= cumulative:
            return fn
    return SCENARIOS[0][0]


def main():
    log.info("=" * 60)
    log.info("APM Demo Trace Generator starting")
    log.info(f"OTel endpoint: {OTEL_ENDPOINT}")
    log.info(f"Services: {list(SERVICES.keys())}")
    log.info("=" * 60)

    # Initial burst: 8 traces to populate Jaeger quickly
    log.info("Generating initial burst of 8 traces...")
    for _ in range(8):
        try:
            fn = weighted_choice()
            fn()
        except Exception as e:
            log.error(f"Scenario error: {e}")
        time.sleep(0.5)

    # Force flush all providers
    for p in providers:
        p.force_flush(timeout_millis=5000)
    log.info("Initial burst flushed. Entering steady-state loop...")

    # Steady state: 1 trace every 8-15 seconds
    cycle = 0
    while True:
        cycle += 1
        try:
            fn = weighted_choice()
            fn()
        except Exception as e:
            log.error(f"Scenario error: {e}")

        # Flush every 5 cycles
        if cycle % 5 == 0:
            for p in providers:
                p.force_flush(timeout_millis=3000)

        delay = random.uniform(8, 15)
        time.sleep(delay)


if __name__ == "__main__":
    main()
