from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import httpx
from datetime import datetime
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

@router.get("")
async def get_logs(
    query: str = Query(..., description="LogQL query"),
    limit: int = Query(100, description="Maximum number of log lines"),
    start: str = Query(..., description="Start time in nanoseconds"),
    end: str = Query(..., description="End time in nanoseconds"),
    direction: str = Query("backward", description="Query direction: forward or backward"),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Proxy logs from Loki's query_range API.
    Expects nanosecond timestamps and LogQL query syntax.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": query,
                "limit": limit,
                "start": start,
                "end": end,
                "direction": direction
            }
            
            loki_url = f"{settings.LOKI_URL}/loki/api/v1/query_range"
            response = await client.get(loki_url, params=params)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Loki returned error: {response.text}"
                )
            
            return response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Loki request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to Loki: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
