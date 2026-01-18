"""
RHINOMETRIC v2.4.0 - Redis Connector
====================================

Conector para Redis (cache, queue, pub/sub).
"""

import asyncio
from redis import asyncio as aioredis
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RedisConnector:
    """Conector para Redis."""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        timeout: int = 5
    ):
        self.host = host
        self.port = port
        self.database = database
        self.password = password
        self.ssl = ssl
        self.timeout = timeout
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testear conexión a Redis.
        
        Returns:
            dict: {success: bool, message: str, details: dict}
        """
        try:
            # Construir URL de conexión
            protocol = "rediss" if self.ssl else "redis"
            auth = f":{self.password}@" if self.password else ""
            url = f"{protocol}://{auth}{self.host}:{self.port}/{self.database}"
            
            # Conectar con timeout
            redis = await asyncio.wait_for(
                aioredis.create_redis_pool(url),
                timeout=self.timeout
            )
            
            # Obtener información del servidor
            info = await redis.info()
            redis_version = info.get('server', {}).get('redis_version', 'Unknown')
            used_memory = info.get('memory', {}).get('used_memory_human', 'Unknown')
            connected_clients = info.get('clients', {}).get('connected_clients', 0)
            
            # Test de PING
            pong = await redis.ping()
            
            redis.close()
            await redis.wait_closed()
            
            return {
                "success": True,
                "message": f"Connected to Redis {redis_version}",
                "details": {
                    "redis_version": redis_version,
                    "used_memory": used_memory,
                    "connected_clients": connected_clients,
                    "database": self.database,
                    "ping": "PONG" if pong else "FAILED"
                }
            }
        
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return {
                "success": False,
                "message": f"Connection timeout ({self.timeout}s)",
                "details": {"error": "timeout"}
            }
        
        except aioredis.AuthError:
            logger.error("Invalid password")
            return {
                "success": False,
                "message": "Invalid password",
                "details": {"error": "authentication_failed"}
            }
        
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error": str(e)}
            }
