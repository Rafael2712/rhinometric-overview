"""
Connector service - handles test_connection logic for HTTP and PostgreSQL.
Isolated from the router so it can be reused by future scheduled checks.

Hardened edition:
  - Shared httpx.Client with connection pooling for health-check workloads
  - Per-request timeout still respected
  - Lifecycle management via get_http_client() / shutdown_http_client()
"""

import time
import logging
import httpx
import psycopg2
from datetime import datetime, timezone
from typing import Tuple, Optional

from security.ssrf_protection import validate_url

logger = logging.getLogger('rhinometric.connector_service')

# ── Shared HTTP client pool ────────────────────────────────────
# A module-level httpx.Client that keeps connections alive across
# consecutive health checks, avoiding repeated TCP/TLS handshakes.
# Thread-safe: httpx.Client is safe for concurrent use from
# multiple threads (it uses urllib3-style connection pooling).

_shared_http_client: Optional[httpx.Client] = None
_shared_http_client_notls: Optional[httpx.Client] = None


def get_http_client(verify: bool = True) -> httpx.Client:
    """Return (or lazily create) the shared httpx.Client for health checks."""
    global _shared_http_client, _shared_http_client_notls
    if verify:
        if _shared_http_client is None or _shared_http_client.is_closed:
            _shared_http_client = httpx.Client(
                follow_redirects=False,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=40,
                    keepalive_expiry=30,
                ),
                # No default timeout — set per-request
            )
            logger.info("[Connector] Shared HTTP client (TLS verify) initialized")
        return _shared_http_client
    else:
        if _shared_http_client_notls is None or _shared_http_client_notls.is_closed:
            _shared_http_client_notls = httpx.Client(
                follow_redirects=False,
                verify=False,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=40,
                    keepalive_expiry=30,
                ),
            )
            logger.info("[Connector] Shared HTTP client (TLS skip) initialized")
        return _shared_http_client_notls


def shutdown_http_clients():
    """Close shared HTTP clients. Called on application shutdown."""
    global _shared_http_client, _shared_http_client_notls
    for client in (_shared_http_client, _shared_http_client_notls):
        if client and not client.is_closed:
            try:
                client.close()
            except Exception:
                pass
    _shared_http_client = None
    _shared_http_client_notls = None
    logger.info("[Connector] Shared HTTP clients shut down")


def test_http_connection(
    url: str,
    method: str = "GET",
    health_path: str = "",
    headers: dict = None,
    auth_type: str = None,
    auth_value: str = None,
    timeout_seconds: int = 10,
    skip_tls_verify: bool = False,
    service_name: str = "",
    use_shared_client: bool = True,
) -> dict:
    """
    Test an HTTP/HTTPS endpoint.
    Returns dict with status, message, response_time_ms, status_code.

    Security:
    - SSRF validation blocks requests to private/internal networks
    - TLS verification enabled by default (skip_tls_verify=False)
    - Redirects are disabled to prevent redirect-based SSRF

    When use_shared_client=True (default for health checks), the module-level
    connection-pooled httpx.Client is reused across checks.
    When use_shared_client=False (e.g. manual test-connection from UI),
    a fresh client is created and closed per call.
    """
    full_url = url.rstrip("/")
    if health_path:
        full_url = f"{full_url}/{health_path.lstrip('/')}"

    # ── SSRF Validation ──────────────────────────────────────── 
    ssrf_result = validate_url(full_url, service_name=service_name)
    if not ssrf_result.is_safe:
        logger.warning(
            f'[SSRF] Blocked HTTP connection test to "{full_url}": '
            f'{ssrf_result.reason}'
        )
        return {
            "success": False,
            "status": "error",
            "message": f"SSRF protection: {ssrf_result.reason}",
            "response_time_ms": 0,
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    req_headers = dict(headers) if headers else {}
    if auth_type == "bearer" and auth_value:
        req_headers["Authorization"] = f"Bearer {auth_value}"
    elif auth_type == "api_key" and auth_value:
        req_headers["X-API-Key"] = auth_value
    elif auth_type == "basic" and auth_value:
        req_headers["Authorization"] = f"Basic {auth_value}"

    # TLS verification ON by default; only skip when explicitly requested
    tls_verify = not skip_tls_verify

    start = time.monotonic()
    try:
        if use_shared_client:
            client = get_http_client(verify=tls_verify)
            resp = _do_http_request(client, method, full_url, req_headers, timeout_seconds)
        else:
            # One-off client for manual test-connection calls
            with httpx.Client(
                timeout=timeout_seconds,
                verify=tls_verify,
                follow_redirects=False,
            ) as client:
                resp = _do_http_request(client, method, full_url, req_headers, timeout_seconds)

        elapsed_ms = (time.monotonic() - start) * 1000
        status_code = resp.status_code

        # Classify HTTP status codes
        if 200 <= status_code < 300:
            status = "up"
            message = f"HTTP {status_code} - {elapsed_ms:.0f}ms"
        elif 300 <= status_code < 400:
            status = "degraded"
            location = resp.headers.get("location", "unknown")
            message = f"HTTP {status_code} redirect to {location} (not followed) - {elapsed_ms:.0f}ms"
        elif 400 <= status_code < 500:
            status = "down"
            message = f"Endpoint responded with HTTP {status_code} in {elapsed_ms:.0f} ms. Please review base URL, health path, method, or authentication settings."
        else:
            status = "down"
            message = f"Endpoint responded with HTTP {status_code} (server error) in {elapsed_ms:.0f} ms."

        return {
            "success": status == "up",
            "status": status,
            "message": message,
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": status_code,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    except httpx.ConnectTimeout:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "status": "down",
            "message": f"Connection timeout after {timeout_seconds}s",
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except httpx.ConnectError as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "status": "down",
            "message": f"Connection refused: {e}",
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "status": "error",
            "message": str(e)[:300],
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def _do_http_request(client: httpx.Client, method: str, url: str, headers: dict, timeout_seconds: int):
    """Execute the actual HTTP request on the given client."""
    req_timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)
    if method.upper() == "POST":
        return client.post(url, headers=headers, timeout=req_timeout)
    elif method.upper() == "HEAD":
        return client.head(url, headers=headers, timeout=req_timeout)
    else:
        return client.get(url, headers=headers, timeout=req_timeout)


def test_postgresql_connection(
    host: str,
    port: int = 5432,
    database_name: str = "postgres",
    username: str = "postgres",
    password: str = "",
    ssl_mode: str = "prefer",
    timeout_seconds: int = 10,
) -> dict:
    """
    Test a PostgreSQL connection.
    Returns dict with status, message, response_time_ms.
    """
    start = time.monotonic()
    conn = None
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=database_name,
            user=username,
            password=password,
            sslmode=ssl_mode or "prefer",
            connect_timeout=timeout_seconds,
        )
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.close()

        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": True,
            "status": "up",
            "message": f"Connected - {version[:80]}",
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    except psycopg2.OperationalError as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        msg = str(e).strip().split("\n")[0][:300]
        return {
            "success": False,
            "status": "down",
            "message": msg,
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "status": "error",
            "message": str(e)[:300],
            "response_time_ms": round(elapsed_ms, 2),
            "status_code": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
