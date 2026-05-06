"""
anomalies_v2_compat.py ? Backward-compatibility shim.

Maps the legacy path /api/anomalies/v2-enriched/* to the Go
anomaly engine, using the same enrichment logic as anomalies_v2_proxy.

This shim exists because the v2.5.x frontend bundle calls
/api/anomalies/v2-enriched/active while the canonical path is
/api/v2/anomalies/active.  Only the URL prefix differs ? behaviour
is identical.

DO NOT modify anomaly scoring, alert routing, or business rules here.
"""
import logging

import httpx
from fastapi import APIRouter, Request, Response, Depends
from routers.auth import get_current_user
from routers.anomalies_v2_proxy import (
    _enrich_response,
    ANOMALY_ENGINE_URL,
    HTTP_TIMEOUT,
)
from models.user import User as UserModel

logger = logging.getLogger("anomalies_v2_compat")

router = APIRouter()


@router.api_route("/v2-enriched/active", methods=["GET"])
@router.api_route("/v2-enriched/{path:path}", methods=["GET"])
async def proxy_anomalies_compat(
    request: Request,
    path: str = "active",
    current_user: UserModel = Depends(get_current_user),
):
    """Compat shim: /api/anomalies/v2-enriched/* -> engine /api/v2/anomalies/*."""
    target_url = f"{ANOMALY_ENGINE_URL}/api/v2/anomalies/{path}"

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                target_url,
                params=dict(request.query_params),
                headers={
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ("host", "connection")
                },
            )

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    enriched = _enrich_response(data)
                    return enriched
                except Exception as e:
                    logger.warning(f"Compat enrichment failed: {e}")
                    return Response(
                        content=resp.content,
                        status_code=resp.status_code,
                        headers=dict(resp.headers),
                    )
            else:
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers={
                        k: v for k, v in resp.headers.items()
                        if k.lower() not in ("transfer-encoding", "connection")
                    },
                )

    except httpx.ConnectError as e:
        logger.error(f"Compat: anomaly engine connection failed: {e}")
        return Response(
            content=b'{"error": "Anomaly engine unavailable"}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Compat proxy error: {e}")
        return Response(
            content=b'{"error": "Internal proxy error"}',
            status_code=502,
            media_type="application/json",
        )
