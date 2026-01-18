"""
Dashboards router for Rhinometric Console.
Fetches dashboard list from Grafana API and provides metadata.
"""
from fastapi import APIRouter, HTTPException
import httpx
from typing import List, Optional
from pydantic import BaseModel
from config import settings

router = APIRouter()

class Dashboard(BaseModel):
    uid: str
    title: str
    uri: str
    url: str
    slug: str
    type: str
    tags: List[str]
    isStarred: bool
    folderId: Optional[int] = None
    folderUid: Optional[str] = None
    folderTitle: Optional[str] = None
    folderUrl: Optional[str] = None

class DashboardsResponse(BaseModel):
    dashboards: List[Dashboard]
    total: int

@router.get("", response_model=DashboardsResponse)
async def get_dashboards():
    """
    Fetch all dashboards from Grafana API.
    Returns list with title, UID, tags, folder info.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Grafana API endpoint for searching dashboards
            grafana_url = f"{settings.GRAFANA_URL}/api/search?type=dash-db"
            
            response = await client.get(grafana_url, timeout=10.0)
            response.raise_for_status()
            
            dashboards_data = response.json()
            
            # Transform to our model format
            dashboards = [
                Dashboard(
                    uid=d.get("uid", ""),
                    title=d.get("title", "Untitled"),
                    uri=d.get("uri", ""),
                    url=d.get("url", ""),
                    slug=d.get("slug", ""),
                    type=d.get("type", "dash-db"),
                    tags=d.get("tags", []),
                    isStarred=d.get("isStarred", False),
                    folderId=d.get("folderId"),
                    folderUid=d.get("folderUid"),
                    folderTitle=d.get("folderTitle"),
                    folderUrl=d.get("folderUrl")
                )
                for d in dashboards_data
            ]
            
            return DashboardsResponse(
                dashboards=dashboards,
                total=len(dashboards)
            )
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboards from Grafana: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/{uid}")
async def get_dashboard_by_uid(uid: str):
    """
    Get specific dashboard metadata by UID.
    """
    try:
        async with httpx.AsyncClient() as client:
            grafana_url = f"{settings.GRAFANA_URL}/api/dashboards/uid/{uid}"
            
            response = await client.get(grafana_url, timeout=10.0)
            response.raise_for_status()
            
            return response.json()
            
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard: {str(e)}"
        )
