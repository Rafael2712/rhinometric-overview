"""
RHINOMETRIC API Connector - RabbitMQ Connector
Version: 2.4.0
License: Proprietary

RabbitMQ connector for on-premise message broker monitoring.
Validates connection, retrieves health status, and collects key metrics.
"""

import asyncio
import aiohttp
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RabbitMQConnector:
    """
    RabbitMQ connector using Management API (HTTP).
    
    Supports:
    - Connection validation
    - Health check
    - Queue statistics
    - Message rates
    - Consumer counts
    
    On-premise philosophy:
    - Validates host is not cloud endpoint
    - Warns if external URL detected
    """
    
    def __init__(self):
        self.name = "RabbitMQ"
        self.version = "2.4.0"
    
    async def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to RabbitMQ Management API.
        
        Args:
            config: {
                'host': str,           # e.g., 'localhost' or '192.168.1.10'
                'port': int,           # Management API port (default: 15672)
                'username': str,       # Admin username
                'password': str,       # Admin password
                'vhost': str,          # Virtual host (default: '/')
                'use_ssl': bool        # SSL/TLS enabled
            }
        
        Returns:
            {
                'success': bool,
                'message': str,
                'details': dict,
                'duration_ms': int
            }
        """
        start_time = datetime.now()
        
        try:
            # Extract config
            host = config.get('host', 'localhost')
            port = config.get('port', 15672)
            username = config.get('username', 'guest')
            password = config.get('password', 'guest')
            vhost = config.get('vhost', '/')
            use_ssl = config.get('use_ssl', False)
            
            # On-premise validation
            cloud_keywords = ['amazonaws.com', 'azure.com', 'cloudamqp.com', 'cloud']
            if any(keyword in host.lower() for keyword in cloud_keywords):
                logger.warning(f"⚠️ Cloud endpoint detected: {host}")
                return {
                    'success': False,
                    'message': 'Cloud endpoint detected (RHINOMETRIC is on-premise only)',
                    'details': {
                        'host': host,
                        'warning': 'Use local RabbitMQ instance for on-premise philosophy'
                    },
                    'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            # Build API URL
            protocol = 'https' if use_ssl else 'http'
            base_url = f"{protocol}://{host}:{port}/api"
            
            # Basic auth
            auth = aiohttp.BasicAuth(username, password)
            
            async with aiohttp.ClientSession(auth=auth) as session:
                # Test 1: Overview endpoint
                async with session.get(f"{base_url}/overview", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 401:
                        return {
                            'success': False,
                            'message': 'Authentication failed',
                            'details': {
                                'error': 'Invalid username or password',
                                'username': username
                            },
                            'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                        }
                    
                    if resp.status != 200:
                        return {
                            'success': False,
                            'message': f'HTTP {resp.status}',
                            'details': {
                                'error': await resp.text()
                            },
                            'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                        }
                    
                    overview = await resp.json()
                
                # Test 2: Get vhost queues
                vhost_encoded = vhost.replace('/', '%2F')
                async with session.get(f"{base_url}/queues/{vhost_encoded}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        queues = await resp.json()
                    else:
                        queues = []
                
                # Extract metrics
                rabbitmq_version = overview.get('rabbitmq_version', 'unknown')
                erlang_version = overview.get('erlang_version', 'unknown')
                
                # Message stats
                message_stats = overview.get('message_stats', {})
                publish_rate = message_stats.get('publish_details', {}).get('rate', 0)
                deliver_rate = message_stats.get('deliver_details', {}).get('rate', 0)
                
                # Queue stats
                total_queues = len(queues)
                total_messages = sum(q.get('messages', 0) for q in queues)
                total_consumers = sum(q.get('consumers', 0) for q in queues)
                
                # Node info
                node_name = overview.get('node', 'unknown')
                
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return {
                    'success': True,
                    'message': f'Connected to RabbitMQ {rabbitmq_version}',
                    'details': {
                        'rabbitmq_version': rabbitmq_version,
                        'erlang_version': erlang_version,
                        'node': node_name,
                        'vhost': vhost,
                        'queues': {
                            'total': total_queues,
                            'messages': total_messages,
                            'consumers': total_consumers
                        },
                        'rates': {
                            'publish_per_sec': round(publish_rate, 2),
                            'deliver_per_sec': round(deliver_rate, 2)
                        },
                        'host': host,
                        'port': port,
                        'on_premise': True
                    },
                    'duration_ms': duration_ms
                }
        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'message': 'Connection timeout (10s)',
                'details': {
                    'error': 'RabbitMQ Management API not responding',
                    'host': config.get('host'),
                    'port': config.get('port', 15672),
                    'suggestion': 'Check if RabbitMQ Management plugin is enabled'
                },
                'duration_ms': 10000
            }
        
        except aiohttp.ClientConnectorError as e:
            return {
                'success': False,
                'message': 'Connection refused',
                'details': {
                    'error': str(e),
                    'host': config.get('host'),
                    'port': config.get('port', 15672),
                    'suggestion': 'Verify RabbitMQ is running and Management API is enabled'
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
        
        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'Connection failed',
                'details': {
                    'error': str(e),
                    'type': type(e).__name__
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
