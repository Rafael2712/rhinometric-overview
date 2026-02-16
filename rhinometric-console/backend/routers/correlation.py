"""
Rhino Core - Correlation API
Endpoints para correlación automática de eventos de observabilidad

Autor: Rhinometric.com
Fecha: 09 de febrero de 2026
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional, List
from services.correlation_engine import get_correlation_engine, CorrelationEngine
from services.audit_logger import log_audit_event
from routers.auth import get_current_user

router = APIRouter()


class CorrelationRequest(BaseModel):
    """Request para correlacionar un evento"""
    event_id: str = Field(..., description="ID único del evento")
    event_timestamp: datetime = Field(..., description="Timestamp del evento (ISO format)")
    event_type: str = Field(..., description="Tipo de evento: anomaly, alert, log, trace")
    event_metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadatos adicionales (host, service, labels)")


class CorrelationResponse(BaseModel):
    """Response con datos correlacionados"""
    event_id: str
    timestamp: str
    event_type: str
    correlation_window: Dict[str, Any]
    metadata: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]
    related_anomalies: List[Dict[str, Any]]
    summary: Dict[str, int]


@router.post("/correlate", response_model=CorrelationResponse)
async def correlate_event(
    request: Request,
    correlation_req: CorrelationRequest,
    current_user = Depends(get_current_user),
    engine: CorrelationEngine = Depends(get_correlation_engine)
):
    """
    Correlaciona un evento con datos de observabilidad en una ventana de tiempo.
    
    **Casos de uso:**
    - Anomalía detectada por IA → buscar métricas, logs, trazas relacionadas
    - Alerta disparada → buscar contexto completo
    - Log de error → buscar métricas y trazas del mismo periodo
    
    **Nivel de correlación actual:** Nivel 1 (timestamp ±5 min)
    
    **Requiere autenticación:** Sí (cualquier rol)
    """
    try:
        # Ejecutar correlación
        result = await engine.correlate_event(
            event_id=correlation_req.event_id,
            event_timestamp=correlation_req.event_timestamp,
            event_type=correlation_req.event_type,
            event_metadata=correlation_req.event_metadata
        )
        
        # Agregar resumen de resultados
        result["summary"] = {
            "metrics_count": len(result.get("metrics", [])),
            "logs_count": len(result.get("logs", [])),
            "traces_count": len(result.get("traces", [])),
            "anomalies_count": len(result.get("related_anomalies", []))
        }
        
        # Audit log
        await log_audit_event(
            category="correlation",
            action="event_correlated",
            user_id=current_user.id,
            username=current_user.username,
            message=f"Event {correlation_req.event_id} correlated",
            ip_address=request.client.host if request.client else None,
            metadata={
                "event_type": correlation_req.event_type,
                "metrics_found": result["summary"]["metrics_count"],
                "logs_found": result["summary"]["logs_count"]
            }
        )
        
        return result
    
    except Exception as e:
        # Audit log de error
        await log_audit_event(
            category="correlation",
            action="event_correlation_failed",
            user_id=current_user.id,
            username=current_user.username,
            message=f"Correlation failed for {correlation_req.event_id}: {str(e)}",
            ip_address=request.client.host if request.client else None,
            status="failure"
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Correlation failed: {str(e)}"
        )


@router.get("/health")
async def correlation_health(
    engine: CorrelationEngine = Depends(get_correlation_engine)
):
    """
    Verifica el estado del motor de correlación.
    
    **No requiere autenticación.**
    """
    return {
        "status": "healthy",
        "engine": "CorrelationEngine v1.0",
        "backends": {
            "victoria_metrics": engine.victoria_metrics_url,
            "prometheus": engine.prometheus_url,
            "loki": engine.loki_url,
            "jaeger": engine.jaeger_url,
            "ai_anomaly": engine.ai_anomaly_url
        },
        "config": {
            "correlation_window_seconds": engine.correlation_window,
            "use_victoria_metrics": engine.use_victoria_metrics
        }
    }


@router.get("/config")
async def get_correlation_config(
    current_user = Depends(get_current_user),
    engine: CorrelationEngine = Depends(get_correlation_engine)
):
    """
    Obtiene la configuración actual del motor de correlación.
    
    **Requiere autenticación:** Sí (cualquier rol)
    """
    return {
        "correlation_window_seconds": engine.correlation_window,
        "correlation_window_minutes": engine.correlation_window / 60,
        "use_victoria_metrics": engine.use_victoria_metrics,
        "tsdb_primary": "VictoriaMetrics" if engine.use_victoria_metrics else "Prometheus",
        "backends": {
            "victoria_metrics": engine.victoria_metrics_url,
            "prometheus": engine.prometheus_url,
            "loki": engine.loki_url,
            "jaeger": engine.jaeger_url,
            "ai_anomaly": engine.ai_anomaly_url
        }
    }
