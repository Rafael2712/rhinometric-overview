from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import httpx
from datetime import datetime, timedelta

from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

def parse_lookback(lookback: str) -> timedelta:
    """Convert lookback string (e.g., '1h', '30m') to timedelta"""
    if not lookback:
        return timedelta(hours=1)
    
    unit = lookback[-1]
    try:
        value = int(lookback[:-1])
    except ValueError:
        return timedelta(hours=1)
    
    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        return timedelta(hours=1)

@router.get("")
async def get_traces(
    limit: int = Query(50, description="Maximum number of traces"),
    lookback: str = Query("1h", description="Time range to look back"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    minDuration: Optional[str] = Query(None, description="Minimum duration filter")
    # current_user: UserModel = Depends(get_current_user)  # Disabled for debugging
):
    """
    Proxy traces from Jaeger's API.
    Returns distributed tracing data for performance analysis.
    
    Jaeger API is much simpler than Tempo - returns complete traces directly!
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Calculate time range
            lookback_delta = parse_lookback(lookback)
            end_time = datetime.now()
            start_time = end_time - lookback_delta
            
            # Convert to microseconds (Jaeger format)
            start_us = int(start_time.timestamp() * 1_000_000)
            end_us = int(end_time.timestamp() * 1_000_000)
            
            # Build Jaeger API parameters
            params = {
                "start": start_us,
                "end": end_us,
                "limit": limit
            }
            
            # Only add service parameter if explicitly specified (not 'all')
            if service and service != 'all':
                params["service"] = service
            
            if minDuration:
                # Convert minDuration from "XXms" to microseconds
                try:
                    duration_ms = int(minDuration.replace('ms', ''))
                    params["minDuration"] = f"{duration_ms * 1000}us"
                except:
                    pass
            
            # If service='all', we need to query all available services
            all_traces = []
            
            if not service or service == 'all':
                # First, get list of services from Jaeger
                services_url = f"{settings.JAEGER_URL}/api/services"
                print(f"[TRACES DEBUG] Fetching services from: {services_url}")
                
                try:
                    services_response = await client.get(services_url)
                    if services_response.status_code == 200:
                        services_data = services_response.json()
                        available_services = services_data.get("data", [])
                        print(f"[TRACES DEBUG] Available services: {available_services}")
                        
                        # Query traces for each service
                        for svc in available_services:
                            svc_params = {**params, "service": svc}
                            traces_url = f"{settings.JAEGER_URL}/api/traces"
                            
                            try:
                                trace_response = await client.get(traces_url, params=svc_params)
                                if trace_response.status_code == 200:
                                    trace_data = trace_response.json()
                                    service_traces = trace_data.get("data", [])
                                    all_traces.extend(service_traces)
                                    print(f"[TRACES DEBUG] Found {len(service_traces)} traces from service '{svc}'")
                            except Exception as e:
                                print(f"[TRACES WARN] Failed to get traces from service '{svc}': {e}")
                                continue
                        
                        # Sort by start time (most recent first) and limit
                        all_traces.sort(key=lambda t: t.get("spans", [{}])[0].get("startTime", 0), reverse=True)
                        all_traces = all_traces[:limit]
                        
                        return {"traces": all_traces, "total": len(all_traces)}
                    else:
                        print(f"[TRACES ERROR] Failed to fetch services, status: {services_response.status_code}")
                        return {"traces": [], "error": "Could not fetch services list"}
                except httpx.ConnectError:
                    print(f"[TRACES ERROR] Could not connect to Jaeger at {services_url}")
                    return {"traces": [], "error": "Jaeger unreachable"}
            else:
                # Query specific service
                jaeger_url = f"{settings.JAEGER_URL}/api/traces"
                
                print(f"[TRACES DEBUG] Jaeger URL: {jaeger_url}")
                print(f"[TRACES DEBUG] Params: {params}")
                
                try:
                    response = await client.get(jaeger_url, params=params)
                except httpx.ConnectError:
                    print(f"[TRACES ERROR] Could not connect to Jaeger at {jaeger_url}")
                    return {"traces": [], "error": "Jaeger unreachable"}
                
                print(f"[TRACES DEBUG] Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[TRACES ERROR] Jaeger error response: {error_text}")
                    return {"traces": [], "error": f"Jaeger returned status {response.status_code}: {error_text}"}
                
                jaeger_data = response.json()
                traces = jaeger_data.get("data", [])
                
                print(f"[TRACES DEBUG] Found {len(traces)} traces from service '{service}'")
                
                return {
                    "traces": traces,
                    "total": len(traces)
                }
            
    except httpx.TimeoutException:
        print("[TRACES ERROR] Jaeger request timeout")
        return {"traces": [], "error": "Jaeger request timeout"}
    except httpx.RequestError as e:
        print(f"[TRACES ERROR] Jaeger request error: {e}")
        return {"traces": [], "error": f"Jaeger not available: {str(e)}"}
    except Exception as e:
        print(f"[TRACES ERROR] Unexpected error: {e}")
        return {"traces": [], "error": f"Internal error: {str(e)}"}


@router.get("/services")
async def get_services():
    """
    Get list of available services from Jaeger.
    Used to populate service filter dropdown with real services.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            services_url = f"{settings.JAEGER_URL}/api/services"
            print(f"[SERVICES DEBUG] Fetching from: {services_url}")
            
            try:
                response = await client.get(services_url)
                
                if response.status_code != 200:
                    print(f"[SERVICES ERROR] Status: {response.status_code}")
                    return {"services": [], "error": f"Jaeger returned status {response.status_code}"}
                
                data = response.json()
                services = data.get("data", [])
                
                print(f"[SERVICES DEBUG] Found {len(services)} services: {services}")
                
                return {
                    "services": services,
                    "total": len(services)
                }
            except httpx.ConnectError:
                print(f"[SERVICES ERROR] Could not connect to Jaeger at {services_url}")
                return {"services": [], "error": "Jaeger unreachable"}
    except Exception as e:
        print(f"[SERVICES ERROR] Unexpected error: {e}")
        return {"services": [], "error": f"Internal error: {str(e)}"}