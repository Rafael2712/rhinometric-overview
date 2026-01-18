"""
RHINOMETRIC v2.4.0 - PostgreSQL Connector
=========================================

Conector para bases de datos PostgreSQL.
"""

import asyncio
import asyncpg
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PostgreSQLConnector:
    """Conector para PostgreSQL."""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        ssl: bool = False,
        timeout: int = 5
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl = ssl
        self.timeout = timeout
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testear conexión a PostgreSQL.
        
        Returns:
            dict: {success: bool, message: str, details: dict}
        """
        try:
            # Crear conexión con timeout
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    ssl='require' if self.ssl else 'prefer'
                ),
                timeout=self.timeout
            )
            
            # Obtener información del servidor
            version = await conn.fetchval('SELECT version()')
            server_version = version.split(',')[0] if version else "Unknown"
            
            # Obtener estadísticas básicas
            db_size = await conn.fetchval(
                'SELECT pg_size_pretty(pg_database_size($1))',
                self.database
            )
            
            tables_count = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            
            await conn.close()
            
            return {
                "success": True,
                "message": f"Connected to PostgreSQL {server_version}",
                "details": {
                    "server_version": server_version,
                    "database": self.database,
                    "database_size": db_size,
                    "tables_count": tables_count,
                    "ssl_enabled": self.ssl
                }
            }
        
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return {
                "success": False,
                "message": f"Connection timeout ({self.timeout}s)",
                "details": {"error": "timeout"}
            }
        
        except asyncpg.InvalidPasswordError:
            logger.error("Invalid credentials")
            return {
                "success": False,
                "message": "Invalid username or password",
                "details": {"error": "authentication_failed"}
            }
        
        except asyncpg.InvalidCatalogNameError:
            logger.error(f"Database '{self.database}' not found")
            return {
                "success": False,
                "message": f"Database '{self.database}' does not exist",
                "details": {"error": "database_not_found"}
            }
        
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """Ejecutar una consulta SQL."""
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            
            result = await conn.fetch(query)
            await conn.close()
            
            return {
                "success": True,
                "data": [dict(row) for row in result],
                "row_count": len(result)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
