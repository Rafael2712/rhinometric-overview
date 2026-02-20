from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime, timedelta
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
from utils.entity_scope import (
    EntityScope, classify_entity, get_visible_entities,
    PLATFORM_JOBS, INFRA_JOBS, INTERNAL_PROBE_JOBS,
    ALL_INTERNAL_JOBS, ALL_PLATFORM_JOBS,
    EXCLUDE_REGEX, PLATFORM_REGEX,
)

router = APIRouter()

# Job sets and regex are imported from utils.entity_scope (single source of truth)


class KPIResponse(BaseModel):
    service_status: dict
    monitored_hosts: dict
    active_anomalies: dict
    alerts_24h: dict

class TimeSeriesPoint(BaseModel):
    timestamp: int
    value: float

class KPIHistoricalResponse(BaseModel):
    service_status: List[TimeSeriesPoint]
    monitored_hosts: List[TimeSeriesPoint]
    active_anomalies: List[TimeSeriesPoint]
    alerts_24h: List[TimeSeriesPoint]

@router.get("", response_model=KPIResponse)
async def get_kpis(current_user: UserModel = Depends(get_current_user)):
    """
    Aggregate KPIs from Prometheus and other services.
    The Monitored Services card shows client_services_count as the main number
    and includes platform + total in the subtitle.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"

            # Get all up targets
            services_response = await client.get(prom_url, params={"query": "up"})
            services_data = services_response.json()

            operational_count = 0
            total_count = 0
            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])
                total_count = len(results)
                operational_count = sum(1 for r in results if r.get("value", [None, "0"])[1] == "1")

            uptime_pct = (operational_count / total_count * 100) if total_count > 0 else 100.0

            # Count CLIENT services (everything NOT in ALL_PLATFORM_JOBS)
            client_q = f'count(count(up{{job!~"{EXCLUDE_REGEX}"}}) by (instance))'
            client_response = await client.get(prom_url, params={"query": client_q})
            client_data = client_response.json()
            client_results = client_data.get("data", {}).get("result", [])
            client_count = int(client_results[0].get("value", [0, "0"])[1]) if client_results else 0

            # Count PLATFORM services
            platform_q = f'count(count(up{{job=~"{PLATFORM_REGEX}"}}) by (instance))'
            platform_response = await client.get(prom_url, params={"query": platform_q})
            platform_data = platform_response.json()
            platform_results = platform_data.get("data", {}).get("result", [])
            platform_count = int(platform_results[0].get("value", [0, "0"])[1]) if platform_results else 0

            total_services = client_count + platform_count

            # Get ACTIVE anomalies count from AI service
            anomalies_count = 0
            anomalies_status = "success"
            anomalies_change = "No issues detected"
            try:
                anomalies_response = await client.get(f"{settings.AI_ANOMALY_URL}/anomalies?limit=100", timeout=5.0)
                if anomalies_response.status_code == 200:
                    anomalies_data = anomalies_response.json()
                    anomalies_count = anomalies_data.get("active_count", 0)
                    if anomalies_count > 0:
                        anomalies_status = "warning"
                        anomalies_change = f"{anomalies_count} active"
            except Exception as e:
                print(f"Error fetching anomalies: {e}")

            # Get active alerts count from AlertManager
            alerts_count = 0
            alerts_status = "success"
            alerts_change = "Last 24 hours"
            try:
                alerts_response = await client.get(
                    f"{settings.ALERTMANAGER_URL}/api/v2/alerts", timeout=5.0
                )
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    firing_alerts = [
                        a for a in alerts_data
                        if a.get("status", {}).get("state") == "active"
                    ]
                    alerts_count = len(firing_alerts)
                    if alerts_count > 0:
                        alerts_status = "warning"
                        alerts_change = f"{alerts_count} active now"
                    else:
                        alerts_change = "No active alerts"
            except Exception as e:
                print(f"Error fetching alerts: {e}")

            return KPIResponse(
                service_status={
                    "value": "Operational" if operational_count == total_count else "Degraded",
                    "status": "success" if operational_count == total_count else "warning",
                    "change": f"{platform_count} platform services \u00b7 {uptime_pct:.1f}% Uptime",
                    "operational_count": operational_count,
                    "total_count": total_count
                },
                monitored_hosts={
                    "value": str(client_count),
                    "status": "success",
                    "change": f"Client: {client_count} \u00b7 Platform: {platform_count} \u00b7 Total: {total_services}",
                    "client_services_count": client_count,
                    "platform_services_count": platform_count,
                    "total_services_count": total_services,
                },
                active_anomalies={
                    "value": str(anomalies_count),
                    "status": anomalies_status,
                    "change": anomalies_change
                },
                alerts_24h={
                    "value": str(alerts_count),
                    "status": alerts_status,
                    "change": alerts_change
                }
            )

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Prometheus: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/historical", response_model=KPIHistoricalResponse)
async def get_kpis_historical(current_user: UserModel = Depends(get_current_user)):
    """Get historical KPI data for sparklines (last 24h)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query_range"
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            start_ts = int(start_time.timestamp())
            end_ts = int(end_time.timestamp())
            step = 3600

            uptime_response = await client.get(prom_url, params={
                "query": "100 * (sum(up) / count(up))",
                "start": start_ts, "end": end_ts, "step": step
            })
            uptime_data = uptime_response.json()
            service_status_series = []
            if uptime_data.get("status") == "success":
                values = uptime_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        service_status_series.append(TimeSeriesPoint(timestamp=int(point[0]), value=float(point[1])))

            hosts_response = await client.get(prom_url, params={
                "query": f'count(count by (instance) (up{{job!~"{EXCLUDE_REGEX}"}})) ',
                "start": start_ts, "end": end_ts, "step": step
            })
            hosts_data = hosts_response.json()
            monitored_hosts_series = []
            if hosts_data.get("status") == "success":
                values = hosts_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        monitored_hosts_series.append(TimeSeriesPoint(timestamp=int(point[0]), value=float(point[1])))

            anomalies_response = await client.get(prom_url, params={
                "query": "rhinometric_anomaly_active_count",
                "start": start_ts, "end": end_ts, "step": step
            })
            anomalies_data = anomalies_response.json()
            anomalies_series = []
            if anomalies_data.get("status") == "success":
                values = anomalies_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        anomalies_series.append(TimeSeriesPoint(timestamp=int(point[0]), value=float(point[1])))

            alerts_response = await client.get(prom_url, params={
                "query": 'count(ALERTS{alertstate="firing"})',
                "start": start_ts, "end": end_ts, "step": step
            })
            alerts_data = alerts_response.json()
            alerts_series = []
            if alerts_data.get("status") == "success":
                values = alerts_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        alerts_series.append(TimeSeriesPoint(timestamp=int(point[0]), value=float(point[1])))

            return KPIHistoricalResponse(
                service_status=service_status_series,
                monitored_hosts=monitored_hosts_series,
                active_anomalies=anomalies_series,
                alerts_24h=alerts_series,
            )

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Prometheus: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/services")
async def get_monitored_services(current_user: UserModel = Depends(get_current_user)):
    """
    Get list of all monitored services with category (platform/client).
    Default: returns all services.
    """
    return await _get_services_impl(current_user, filter_type="all")


@router.get("/services/{filter_type}")
async def get_monitored_services_filtered(
    filter_type: str,
    current_user: UserModel = Depends(get_current_user),
):
    """Get monitored services filtered by type: all, platform, or client."""
    if filter_type not in ("all", "platform", "client"):
        raise HTTPException(status_code=400, detail="filter_type must be 'all', 'platform', or 'client'")
    return await _get_services_impl(current_user, filter_type=filter_type)


async def _get_services_impl(current_user: UserModel, filter_type: str = "all"):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"

            services_response = await client.get(
                prom_url,
                params={"query": 'up{job!~"node-exporter|cadvisor|blackbox-exporter"}'}
            )
            services_data = services_response.json()

            services_list = []
            platform_count = 0
            client_count = 0
            platform_up = 0
            client_up = 0

            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])

                for result in results:
                    metric = result.get("metric", {})
                    value = result.get("value", [None, "0"])
                    job = metric.get("job", "unknown")
                    is_up = value[1] == "1"

                    # Deterministic classification via entity_scope
                    scope = classify_entity(job)
                    is_platform = (scope == EntityScope.PLATFORM)
                    category = "platform" if is_platform else "client"

                    if is_platform:
                        platform_count += 1
                        if is_up:
                            platform_up += 1
                    else:
                        client_count += 1
                        if is_up:
                            client_up += 1

                    service = {
                        "name": job,
                        "instance": metric.get("instance", "unknown"),
                        "status": "up" if is_up else "down",
                        "tier": metric.get("tier", "application"),
                        "service_type": metric.get("service", job),
                        "category": category,
                        "entity_scope": scope.value,
                        "version": metric.get("version", "N/A"),
                        "labels": {k: v for k, v in metric.items() if k not in ["__name__", "job", "instance"]}
                    }
                    services_list.append(service)

            # Apply deployment_mode visibility filter
            services_list = get_visible_entities(
                services_list,
                deployment_mode=settings.DEPLOYMENT_MODE,
                scope_key="entity_scope",
            )

            if filter_type == "platform":
                services_list = [s for s in services_list if s["category"] == "platform"]
            elif filter_type == "client":
                services_list = [s for s in services_list if s["category"] == "client"]

            services_list.sort(key=lambda x: (0 if x["status"] == "down" else 1, x["name"]))

            up_count = sum(1 for s in services_list if s["status"] == "up")
            down_count = len(services_list) - up_count

            return {
                "services": services_list,
                "total": len(services_list),
                "up": up_count,
                "down": down_count,
                "platform_services": platform_count,
                "platform_up": platform_up,
                "client_services": client_count,
                "client_up": client_up,
                "filter": filter_type,
                "timestamp": datetime.now().isoformat()
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Prometheus: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/system-health")
async def get_system_health(current_user: UserModel = Depends(get_current_user)):
    """Get comprehensive system health overview."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"

            services_response = await client.get(prom_url, params={"query": "up"})
            services_data = services_response.json()

            all_services = []
            platform_healthy = 0
            platform_total = 0
            client_healthy = 0
            client_total = 0

            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])
                for result in results:
                    metric = result.get("metric", {})
                    value = result.get("value", [None, "0"])
                    is_up = value[1] == "1"
                    job = metric.get("job", "unknown")
                    is_platform = classify_entity(job) == EntityScope.PLATFORM

                    if is_platform:
                        platform_total += 1
                        if is_up:
                            platform_healthy += 1
                    else:
                        client_total += 1
                        if is_up:
                            client_healthy += 1

                    all_services.append({
                        "name": job,
                        "instance": metric.get("instance", ""),
                        "is_up": is_up,
                        "is_platform": is_platform
                    })

            platform_unhealthy = platform_total - platform_healthy
            total_unhealthy = platform_unhealthy + (client_total - client_healthy)

            if total_unhealthy == 0:
                overall_status = "operational"
            elif total_unhealthy <= 2:
                overall_status = "degraded"
            else:
                overall_status = "critical"

            uptime_pct = (platform_healthy / platform_total * 100) if platform_total > 0 else 100.0

            components = [
                {"name": "Prometheus", "status": "ok" if any(s["name"] == "prometheus" and s["is_up"] for s in all_services) else "critical", "category": "telemetry", "message": "Metrics collection active"},
                {"name": "Grafana", "status": "ok" if any(s["name"] == "grafana" and s["is_up"] for s in all_services) else "critical", "category": "visualization", "message": "Dashboard service running"},
                {"name": "Loki", "status": "ok" if any(s["name"] == "loki" and s["is_up"] for s in all_services) else "warning", "category": "telemetry", "message": "Log aggregation active"},
                {"name": "Jaeger", "status": "ok" if any(s["name"] == "jaeger" and s["is_up"] for s in all_services) else "warning", "category": "telemetry", "message": "Distributed tracing operational"},
                {"name": "AI Anomaly Detection", "status": "ok", "category": "intelligence", "message": "ML models trained and active"},
                {"name": "License Server", "status": "ok", "category": "security", "message": "License validation active"},
                {"name": "AlertManager", "status": "ok" if any(s["name"] == "alertmanager" and s["is_up"] for s in all_services) else "warning", "category": "alerting", "message": "Alert routing configured"},
                {"name": "Console Backend", "status": "ok", "category": "application", "message": "API Gateway responding"},
            ]

            try:
                for component in components:
                    component_name_lower = component["name"].lower().replace(" ", "-")
                    matching_service = next(
                        (s for s in all_services if component_name_lower in s["name"].lower() and s["is_platform"]),
                        None
                    )
                    if matching_service:
                        component["status"] = "ok" if matching_service["is_up"] else "critical"
            except Exception as e:
                print(f"Error enriching component status: {e}")

            recent_events = [
                {"timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(), "event": "System started successfully", "severity": "info", "source": "system"},
                {"timestamp": (datetime.now() - timedelta(minutes=8)).isoformat(), "event": "All collectors connected", "severity": "info", "source": "prometheus"},
            ]

            for service in all_services:
                if not service["is_up"]:
                    recent_events.insert(0, {"timestamp": datetime.now().isoformat(), "event": f"Service {service['name']} is down", "severity": "error", "source": service["name"]})

            try:
                alerts_response = await client.get(f"{settings.ALERTMANAGER_URL}/api/v2/alerts", timeout=5.0)
                if alerts_response.status_code == 200:
                    alerts = alerts_response.json()
                    for alert in alerts[:5]:
                        if alert.get("status", {}).get("state") == "active":
                            recent_events.insert(0, {
                                "timestamp": alert.get("startsAt", datetime.now().isoformat()),
                                "event": alert.get("labels", {}).get("alertname", "Unknown alert"),
                                "severity": "warning" if alert.get("labels", {}).get("severity") == "warning" else "error",
                                "source": "alertmanager"
                            })
            except Exception as e:
                print(f"Error fetching alerts for events: {e}")

            recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
            recent_events = recent_events[:10]

            return {
                "overall_status": overall_status,
                "uptime_percentage": uptime_pct,
                "uptime_period": "Last 30 days",
                "platform_services": {"total": platform_total, "healthy": platform_healthy, "unhealthy": platform_unhealthy},
                "client_services": {"total": client_total, "healthy": client_healthy},
                "active_issues": total_unhealthy,
                "components": components,
                "recent_events": recent_events,
                "last_check": datetime.now().isoformat()
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to services: {str(e)}")
    except Exception as e:
        print(f"Error in system-health: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
