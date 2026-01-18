"""
Grafana API Client
Handles all interactions with Grafana API for dashboard management
"""
import logging
from typing import Dict, List, Optional, Any
import httpx
from config import config

logger = logging.getLogger(__name__)


class GrafanaClient:
    """Grafana API client for dashboard operations"""
    
    def __init__(self):
        self.base_url = config.grafana.url
        self.auth = (config.grafana.username, config.grafana.password)
        self.timeout = config.grafana.timeout
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Grafana API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def create_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard in Grafana"""
        payload = {
            "dashboard": dashboard,
            "overwrite": False,
            "message": "Created via Dashboard Builder"
        }
        
        result = await self._request("POST", "/api/dashboards/db", json_data=payload)
        logger.info(f"Dashboard created: {result.get('uid')}")
        return result
    
    async def update_dashboard(
        self,
        dashboard: Dict[str, Any],
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Update existing dashboard"""
        payload = {
            "dashboard": dashboard,
            "overwrite": overwrite,
            "message": "Updated via Dashboard Builder"
        }
        
        result = await self._request("POST", "/api/dashboards/db", json_data=payload)
        logger.info(f"Dashboard updated: {result.get('uid')}")
        return result
    
    async def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """Get dashboard by UID"""
        result = await self._request("GET", f"/api/dashboards/uid/{uid}")
        return result.get("dashboard", {})
    
    async def delete_dashboard(self, uid: str) -> Dict[str, Any]:
        """Delete dashboard by UID"""
        result = await self._request("DELETE", f"/api/dashboards/uid/{uid}")
        logger.info(f"Dashboard deleted: {uid}")
        return result
    
    async def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all dashboards"""
        result = await self._request("GET", "/api/search", params={"type": "dash-db"})
        return result
    
    async def get_folders(self) -> List[Dict[str, Any]]:
        """Get all folders"""
        result = await self._request("GET", "/api/folders")
        return result
    
    async def create_folder(self, title: str) -> Dict[str, Any]:
        """Create a new folder"""
        payload = {"title": title}
        result = await self._request("POST", "/api/folders", json_data=payload)
        logger.info(f"Folder created: {title}")
        return result
    
    async def get_datasources(self) -> List[Dict[str, Any]]:
        """Get all datasources"""
        result = await self._request("GET", "/api/datasources")
        return result
    
    async def test_connection(self) -> bool:
        """Test connection to Grafana"""
        try:
            await self._request("GET", "/api/health")
            return True
        except Exception as e:
            logger.error(f"Grafana connection failed: {e}")
            return False


# Global client instance
grafana_client = GrafanaClient()
