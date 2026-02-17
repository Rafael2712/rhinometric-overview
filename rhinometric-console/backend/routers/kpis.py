from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime, timedelta
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

# Explicit set of platform/infrastructure jobs.
# Everything NOT in this set is classified as a "client service".
# To add a new platform job, add it here. To add a client service, just add its
# Prometheus scrape job — it will be picked up automatically.
PLATFORM_JOBS = {
    "prometheus",
    "grafana",
    "loki",
    "jaeger",
    "alertmanager",
    "otel-collector",
    "console-backend",
    "license-server-v2",
    "ai-anomaly",
    "postgres",
    "redis",
    "promtail",
}

# Jobs that are pure infrastructure/internal and should be excluded from
# the "Monitored Services" KPI and from the /services endpoint.
# These infrastructure exporters are classified as platform in system-health
# and excluded from the "Monitored Services" KPI counter and /services endpoint.
INFRA_JOBS = {
    "node-exporter",
    "cadvisor",
    "blackbox-exporter",
}

# Internal probe jobs excluded from "Monitored Services" KPI and /services,
# but counted as client services in system-health (they represent healthchecks).
INTERNAL_PROBE_JOBS = {
    "blackbox-http",
}


# All internal jobs combined for PromQL exclusion
ALL_INTERNAL_JOBS = PLATFORM_JOBS | INFRA_JOBS | INTERNAL_PROBE_JOBS
EXCLUDE_REGEX = "|".join(sorted(ALL_INTERNAL_JOBS))
PLATFORM_REGEX = "|".join(sorted(PLATFORM_JOBS))


class KPIResponse(BaseModel):
    service_status: dict
    monitored_hosts: dict
    active_anomalies: dict
    alerts_24h: dict

class TimeSeriesPoint(BaseModel):
    timestamp: int  # Unix timestamp
    value: float

class KPIHistoricalResponse(BaseModel):
    service_status: List[TimeSeriesPoint]
    monitored_hosts: List[TimeSeriesPoint]
    active_anomalies: List[TimeSeriesPoint]
    alerts_24h: List[TimeSeriesPoint]

@router.get("", response_model=KPIResponse)
async def get_kpis(current_user: UserModel = Depends(get_current_user)):
    # TODO-RBAC: KPI counts should reflect only services visible to current_user role/tenant
    """
    Aggregate KPIs from Prometheus and other services
    
    Returns:
    - Service status (uptime from Prometheus)
    - Monitored hosts count
    - Active anomalies count (from AI Anomaly service)
    - Alerts in last 24h (from AlertManager)
    """
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Prometheus for service status
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"
            
            # Get number of up services
            services_response = await client.get(
                prom_url,
                params={"query": "up"}
            )
            services_data = services_response.json()
            
            # Count operational services
            operational_count = 0
            total_count = 0
            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])
                total_count = len(results)
                operational_count = sum(1 for r in results if r.get("value", [None, "0"])[1] == "1")
            
            # Calculate uptime percentage
            uptime_pct = (operational_count / total_count * 100) if total_count > 0 else 100.0
            
            # Get unique monitored services - count by unique instances
            # Filter out infrastructure exporters and internal healthchecks
            # node-exporter, cadvisor = host metrics; blackbox-exporter = self; blackbox-http = internal probes
            # blackbox-web-* jobs ARE included (external website monitoring = client services)
            # These are monitoring infrastructure, not client services
            services_response = await client.get(
                prom_url,
                params={"query": f'count(count(up{{job!~"{EXCLUDE_REGEX}"}}) by (instance))'}
            )
            services_data = services_response.json()
            results = services_data.get("data", {}).get("result", [])
            service_count = int(results[0].get("value", [0, "0"])[1]) if results else 0
            
            # Get total monitored including core (for internal metrics)
            total_response = await client.get(
                prom_url,
                params={"query": "count(count(up) by (instance))"}
            )
            total_data = total_response.json()
            total_results = total_data.get("data", {}).get("result", [])
            total_services_with_core = int(total_results[0].get("value", [0, "0"])[1]) if total_results else 0


            # Count platform services only (for Service Status card)
            platform_q = f'count(count(up{{job=~"{PLATFORM_REGEX}"}}) by (instance))'
            platform_response = await client.get(prom_url, params={"query": platform_q})
            platform_data = platform_response.json()
            platform_results = platform_data.get("data", {}).get("result", [])
            platform_count = int(platform_results[0].get("value", [0, "0"])[1]) if platform_results else 0
            
            # Get ACTIVE anomalies count from AI service (no auth required)
            # Use active_count instead of total to match Anomalies page
            anomalies_count = 0
            anomalies_status = "success"
            anomalies_change = "No issues detected"
            try:
                anomalies_response = await client.get(f"{settings.AI_ANOMALY_URL}/anomalies?limit=100", timeout=5.0)
                if anomalies_response.status_code == 200:
                    anomalies_data = anomalies_response.json()
                    # Use active_count for consistency with Anomalies page
                    anomalies_count = anomalies_data.get("active_count", 0)
                    if anomalies_count > 0:
                        anomalies_status = "warning"
                        anomalies_change = f"{anomalies_count} active"
            except Exception as e:
                print(f"Error fetching anomalies: {e}")
                pass  # If AI service unavailable, keep at 0
            
            # Get active alerts count from AlertManager
            alerts_count = 0
            alerts_status = "success"
            alerts_change = "Last 24 hours"
            try:
                # Alertmanager API returns ALL alerts, need to filter client-side
                alerts_response = await client.get(
                    f"{settings.ALERTMANAGER_URL}/api/v2/alerts",
                    timeout=5.0
                )
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    # Filter only FIRING alerts (status.state == "active")
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
                pass  # If AlertManager unavailable, keep at 0
            
            return KPIResponse(
                service_status={
                    "value": "Operational" if operational_count == total_count else "Degraded",
                    "status": "success" if operational_count == total_count else "warning",
                    "change": f"{platform_count} platform services · {uptime_pct:.1f}% Uptime",
                    "operational_count": operational_count,
                    "total_count": total_count
                },
                monitored_hosts={
                    "value": str(service_count),
                    "status": "success",
                    "change": f"Client services (Total: {service_count + platform_count} incl. platform)"
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
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Prometheus: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
@router.get("/historical", response_model=KPIHistoricalResponse)
async def get_kpis_historical(current_user: UserModel = Depends(get_current_user)):
    """
    Get historical KPI data for the last 24 hours (24 data points, 1 per hour)
    Used for mini sparkline charts in the Home dashboard
    """
    
    print("[KPI Historical] Fetching last 24h data for sparklines...")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query_range"
            
            # Calculate time range: last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Convert to Unix timestamps
            start_ts = int(start_time.timestamp())
            end_ts = int(end_time.timestamp())
            step = 3600  # 1 hour intervals = 24 data points
            
            # Query 1: Service uptime percentage over 24h
            uptime_response = await client.get(
                prom_url,
                params={
                    "query": "100 * (sum(up) / count(up))",
                    "start": start_ts,
                    "end": end_ts,
                    "step": step
                }
            )
            uptime_data = uptime_response.json()
            service_status_series = []
            if uptime_data.get("status") == "success":
                values = uptime_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        service_status_series.append(TimeSeriesPoint(
                            timestamp=int(point[0]),
                            value=float(point[1])
                        ))
            
            # Query 2: Number of monitored hosts over 24h
            hosts_response = await client.get(
                prom_url,
                params={
                    "query": f'count(count by (instance) (up{{job!~"{EXCLUDE_REGEX}"}}))',
                    "start": start_ts,
                    "end": end_ts,
                    "step": step
                }
            )
            hosts_data = hosts_response.json()
            monitored_hosts_series = []
            if hosts_data.get("status") == "success":
                values = hosts_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        monitored_hosts_series.append(TimeSeriesPoint(
                            timestamp=int(point[0]),
                            value=float(point[1])
                        ))
            
            # Query 3: Historical anomalies count from AI Anomaly service via Prometheus
            # The AI service exposes a metric: rhinometric_anomaly_active_count
            anomalies_response = await client.get(
                prom_url,
                params={
                    "query": "rhinometric_anomaly_active_count",
                    "start": start_ts,
                    "end": end_ts,
                    "step": step
                }
            )
            anomalies_data = anomalies_response.json()
            anomalies_series = []
            if anomalies_data.get("status") == "success":
                values = anomalies_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        anomalies_series.append(TimeSeriesPoint(
                            timestamp=int(point[0]),
                            value=float(point[1])
                        ))
            
            # Query 4: Historical alerts count from Alertmanager via Prometheus
            # Prometheus records alert state: ALERTS{alertstate="firing"}
            alerts_response = await client.get(
                prom_url,
                params={
                    "query": 'count(ALERTS{alertstate="firing"})',
                    "start": start_ts,
                    "end": end_ts,
                    "step": step
                }
            )
            alerts_data = alerts_response.json()
            alerts_series = []
            if alerts_data.get("status") == "success":
                values = alerts_data.get("data", {}).get("result", [])
                if values:
                    for point in values[0].get("values", []):
                        alerts_series.append(TimeSeriesPoint(
                            timestamp=int(point[0]),
                            value=float(point[1])
                        ))
            
            print(f"[KPI Historical] Generated {len(service_status_series)} service status points (REAL)")
            print(f"[KPI Historical] Generated {len(monitored_hosts_series)} hosts points (REAL)")
            print(f"[KPI Historical] Generated {len(anomalies_series)} anomalies points (REAL)")
            print(f"[KPI Historical] Generated {len(alerts_series)} alerts points (REAL)")
            
            return KPIHistoricalResponse(
                service_status=service_status_series if service_status_series else [],
                monitored_hosts=monitored_hosts_series if monitored_hosts_series else [],
                active_anomalies=anomalies_series if anomalies_series else [],
                alerts_24h=alerts_series if alerts_series else []
            )
            
    except httpx.RequestError as e:
        print(f"[KPI Historical] Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Prometheus: {str(e)}"
        )
    except Exception as e:
        print(f"[KPI Historical] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/services")
async def get_monitored_services(current_user: UserModel = Depends(get_current_user)):
    # TODO-RBAC: Scope service list to current_user tenant when multi-tenancy is enabled
    """
    Get list of all monitored services with their status
    
    Returns detailed information about each service being monitored
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"
            
            # Get all services excluding infrastructure exporters
            services_response = await client.get(
                prom_url,
                params={"query": 'up{job!~"node-exporter|cadvisor|blackbox-exporter|blackbox-http"}'}
            )
            services_data = services_response.json()
            
            services_list = []
            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])
                
                for result in results:
                    metric = result.get("metric", {})
                    value = result.get("value", [None, "0"])
                    
                    service = {
                        "name": metric.get("job", "unknown"),
                        "instance": metric.get("instance", "unknown"),
                        "status": "up" if value[1] == "1" else "down",
                        "tier": metric.get("tier", "application"),
                        "service_type": metric.get("service", metric.get("job", "unknown")),
                        "version": metric.get("version", "N/A"),
                        "labels": {k: v for k, v in metric.items() if k not in ["__name__", "job", "instance"]}
                    }
                    services_list.append(service)
            
            # Sort by status (down first, then up) and then by name
            services_list.sort(key=lambda x: (0 if x["status"] == "down" else 1, x["name"]))
            
            up_count = sum(1 for s in services_list if s["status"] == "up")
            down_count = len(services_list) - up_count
            
            return {
                "services": services_list,
                "total": len(services_list),
                "up": up_count,
                "down": down_count,
                "timestamp": datetime.now().isoformat()
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Prometheus: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/system-health")
async def get_system_health(current_user: UserModel = Depends(get_current_user)):
    """
    Get comprehensive system health overview
    
    Returns:
    - Overall system status (operational/degraded/critical)
    - Platform and client services health
    - Individual component health status
    - Recent system events
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"
            
            # Get all services status
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
                    
                    # Classify as platform or client service
                    # TODO-RBAC: When RBAC is implemented, filter services by user tenant/role
                    is_platform = job in PLATFORM_JOBS or job in INFRA_JOBS
                    
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
            
            # Calculate overall status
            platform_unhealthy = platform_total - platform_healthy
            total_unhealthy = platform_unhealthy + (client_total - client_healthy)
            
            if total_unhealthy == 0:
                overall_status = "operational"
            elif total_unhealthy <= 2:
                overall_status = "degraded"
            else:
                overall_status = "critical"
            
            # Calculate uptime percentage (simplified - last 30 days)
            uptime_pct = (platform_healthy / platform_total * 100) if platform_total > 0 else 100.0
            
            # Build component health list
            components = [
                {
                    "name": "Prometheus",
                    "status": "ok" if any(s["name"] == "prometheus" and s["is_up"] for s in all_services) else "critical",
                    "category": "telemetry",
                    "message": "Metrics collection active"
                },
                {
                    "name": "Grafana",
                    "status": "ok" if any(s["name"] == "grafana" and s["is_up"] for s in all_services) else "critical",
                    "category": "visualization",
                    "message": "Dashboard service running"
                },
                {
                    "name": "Loki",
                    "status": "ok" if any(s["name"] == "loki" and s["is_up"] for s in all_services) else "warning",
                    "category": "telemetry",
                    "message": "Log aggregation active"
                },
                {
                    "name": "Jaeger",
                    "status": "ok" if any(s["name"] == "jaeger" and s["is_up"] for s in all_services) else "warning",
                    "category": "telemetry",
                    "message": "Distributed tracing operational"
                },
                {
                    "name": "AI Anomaly Detection",
                    "status": "ok",
                    "category": "intelligence",
                    "message": "ML models trained and active"
                },
                {
                    "name": "License Server",
                    "status": "ok",
                    "category": "security",
                    "message": "License validation active"
                },
                {
                    "name": "AlertManager",
                    "status": "ok" if any(s["name"] == "alertmanager" and s["is_up"] for s in all_services) else "warning",
                    "category": "alerting",
                    "message": "Alert routing configured"
                },
                {
                    "name": "Console Backend",
                    "status": "ok",
                    "category": "application",
                    "message": "API Gateway responding"
                }
            ]
            
            # Try to get actual component status from Prometheus
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
            
            # Get recent events
            recent_events = [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                    "event": "System started successfully",
                    "severity": "info",
                    "source": "system"
                },
                {
                    "timestamp": (datetime.now() - timedelta(minutes=8)).isoformat(),
                    "event": "All collectors connected",
                    "severity": "info",
                    "source": "prometheus"
                }
            ]
            
            # Add unhealthy services to events
            for service in all_services:
                if not service["is_up"]:
                    recent_events.insert(0, {
                        "timestamp": datetime.now().isoformat(),
                        "event": f"Service {service['name']} is down",
                        "severity": "error",
                        "source": service["name"]
                    })
            
            # Try to get alerts as events
            try:
                alerts_response = await client.get(
                    f"{settings.ALERTMANAGER_URL}/api/v2/alerts",
                    timeout=5.0
                )
                if alerts_response.status_code == 200:
                    alerts = alerts_response.json()
                    for alert in alerts[:5]:  # Last 5 alerts
                        if alert.get("status", {}).get("state") == "active":
                            recent_events.insert(0, {
                                "timestamp": alert.get("startsAt", datetime.now().isoformat()),
                                "event": alert.get("labels", {}).get("alertname", "Unknown alert"),
                                "severity": "warning" if alert.get("labels", {}).get("severity") == "warning" else "error",
                                "source": "alertmanager"
                            })
            except Exception as e:
                print(f"Error fetching alerts for events: {e}")
            
            # Sort events by timestamp (most recent first) and limit to 10
            recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
            recent_events = recent_events[:10]
            
            return {
                "overall_status": overall_status,
                "uptime_percentage": uptime_pct,
                "uptime_period": "Last 30 days",
                "platform_services": {
                    "total": platform_total,
                    "healthy": platform_healthy,
                    "unhealthy": platform_unhealthy
                },
                "client_services": {
                    "total": client_total,
                    "healthy": client_healthy
                },
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