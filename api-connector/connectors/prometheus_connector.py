"""
RHINOMETRIC v2.4.0 - Prometheus Connector
=========================================

Conector para Prometheus metrics server.
"""

import aiohttp
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PrometheusConnector:
    """Conector para Prometheus."""
    
    def __init__(self, url: str, timeout: int = 30):
        self.url = url.rstrip('/')
        self.timeout = timeout
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testear conexión a Prometheus.
        
        Returns:
            dict: {success: bool, message: str, details: dict}
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get(
                    f"{self.url}/-/healthy",
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        health_status = "healthy"
                    else:
                        health_status = f"unhealthy (HTTP {response.status})"
                
                # Build info
                async with session.get(
                    f"{self.url}/api/v1/status/buildinfo",
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        build_info = await response.json()
                        version = build_info.get('data', {}).get('version', 'Unknown')
                    else:
                        version = "Unknown"
                
                # Runtime info
                async with session.get(
                    f"{self.url}/api/v1/status/runtimeinfo",
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        runtime_info = await response.json()
                        storage_retention = runtime_info.get('data', {}).get('storageRetention', 'Unknown')
                    else:
                        storage_retention = "Unknown"
                
                return {
                    "success": True,
                    "message": f"Connected to Prometheus {version}",
                    "details": {
                        "version": version,
                        "health_status": health_status,
                        "storage_retention": storage_retention,
                        "url": self.url
                    }
                }
        
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.url}")
            return {
                "success": False,
                "message": f"Connection timeout ({self.timeout}s)",
                "details": {"error": "timeout"}
            }
        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection refused: {str(e)}")
            return {
                "success": False,
                "message": f"Cannot connect to {self.url}",
                "details": {"error": "connection_refused"}
            }
        
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def query(self, query: str) -> Dict[str, Any]:
        """Ejecutar una consulta PromQL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/v1/query",
                    params={"query": query},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "data": data.get('data', {})
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}"
                        }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
