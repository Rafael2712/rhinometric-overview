"""
Connector service - handles test_connection logic for HTTP and PostgreSQL.
Isolated from the router so it can be reused by future scheduled checks.
"""

import time
import logging
import httpx
import psycopg2
from datetime import datetime, timezone
from typing import Tuple

from security.ssrf_protection import validate_url

logger = logging.getLogger('rhinometric.connector_service')


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
) -> dict:
    """
    Test an HTTP/HTTPS endpoint.
    Returns dict with status, message, response_time_ms, status_code.

    Security:
    - SSRF validation blocks requests to private/internal networks
    - TLS verification enabled by default (skip_tls_verify=False)
    - Redirects are disabled to prevent redirect-based SSRF
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
        with httpx.Client(
            timeout=timeout_seconds,
            verify=tls_verify,
            follow_redirects=False,
        ) as client:
            if method.upper() == "POST":
                resp = client.post(full_url, headers=req_headers)
            elif method.upper() == "HEAD":
                resp = client.head(full_url, headers=req_headers)
            else:
                resp = client.get(full_url, headers=req_headers)

        elapsed_ms = (time.monotonic() - start) * 1000
        status_code = resp.status_code

        # Treat 3xx as informational (redirects are blocked, so report them)
        if 200 <= status_code < 300:
            status = "up"
            message = f"HTTP {status_code} - {elapsed_ms:.0f}ms"
        elif 300 <= status_code < 400:
            status = "degraded"
            location = resp.headers.get("location", "unknown")
            message = f"HTTP {status_code} redirect to {location} (not followed) - {elapsed_ms:.0f}ms"
        elif 400 <= status_code < 500:
            status = "degraded"
            message = f"HTTP {status_code} client error - {elapsed_ms:.0f}ms"
        else:
            status = "down"
            message = f"HTTP {status_code} server error - {elapsed_ms:.0f}ms"

        return {
            "success": status in ("up", "degraded"),
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