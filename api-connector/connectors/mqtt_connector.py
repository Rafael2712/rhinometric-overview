"""
RHINOMETRIC API Connector - MQTT Connector
Version: 2.4.0
License: Proprietary

MQTT connector for on-premise IoT and messaging monitoring.
Validates connection, subscribes to topics, and collects broker metrics.
"""

import asyncio
from typing import Dict, Any
import logging
from datetime import datetime
import aiomqtt

logger = logging.getLogger(__name__)


class MQTTConnector:
    """
    MQTT connector using asyncio-mqtt library.
    
    Supports:
    - Connection validation
    - Broker ping
    - Topic subscription test
    - QoS levels
    - Clean session
    
    On-premise philosophy:
    - Validates broker is local
    - Warns if public brokers detected
    """
    
    def __init__(self):
        self.name = "MQTT"
        self.version = "2.4.0"
    
    async def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to MQTT broker.
        
        Args:
            config: {
                'host': str,              # e.g., 'localhost' or '192.168.1.10'
                'port': int,              # Default: 1883 (non-SSL) or 8883 (SSL)
                'username': str,          # Optional username
                'password': str,          # Optional password
                'client_id': str,         # Optional client ID
                'use_tls': bool,          # Enable TLS/SSL
                'keepalive': int,         # Keepalive interval (seconds)
                'clean_session': bool,    # Clean session flag
                'test_topic': str         # Topic to subscribe for testing
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
            port = config.get('port', 1883)
            username = config.get('username')
            password = config.get('password')
            client_id = config.get('client_id', 'rhinometric-connector')
            use_tls = config.get('use_tls', False)
            keepalive = config.get('keepalive', 60)
            clean_session = config.get('clean_session', True)
            test_topic = config.get('test_topic', 'rhinometric/test')
            
            # On-premise validation
            public_brokers = ['test.mosquitto.org', 'broker.hivemq.com', 'mqtt.eclipse.org']
            cloud_keywords = ['amazonaws.com', 'azure.com', 'cloudmqtt.com']
            
            if host.lower() in public_brokers or any(keyword in host.lower() for keyword in cloud_keywords):
                logger.warning(f"⚠️ Public/cloud broker detected: {host}")
                return {
                    'success': False,
                    'message': 'Public/cloud broker detected (RHINOMETRIC is on-premise only)',
                    'details': {
                        'host': host,
                        'warning': 'Use local MQTT broker (Mosquitto, EMQX, etc.) for on-premise philosophy'
                    },
                    'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            # Build connection parameters
            tls_context = None
            if use_tls:
                import ssl
                tls_context = ssl.create_default_context()
                # For self-signed certificates, you might want:
                # tls_context.check_hostname = False
                # tls_context.verify_mode = ssl.CERT_NONE
            
            # Connect to broker
            async with aiomqtt.Client(
                hostname=host,
                port=port,
                username=username,
                password=password,
                identifier=client_id,
                keepalive=keepalive,
                clean_session=clean_session,
                tls_context=tls_context,
                timeout=10
            ) as client:
                
                # Test 1: Connection successful (implicit by context manager)
                connect_duration = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # Test 2: Subscribe to test topic
                await asyncio.wait_for(
                    client.subscribe(test_topic),
                    timeout=5
                )
                
                # Test 3: Publish test message
                test_message = f"RHINOMETRIC test at {datetime.now().isoformat()}"
                await asyncio.wait_for(
                    client.publish(test_topic, test_message, qos=1),
                    timeout=5
                )
                
                # Test 4: Wait for message (with timeout)
                message_received = False
                try:
                    async with asyncio.timeout(3):
                        async for message in client.messages:
                            if message.topic.matches(test_topic):
                                message_received = True
                                break
                except asyncio.TimeoutError:
                    pass  # Message not received, but connection is valid
                
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return {
                    'success': True,
                    'message': f'Connected to MQTT broker',
                    'details': {
                        'broker': {
                            'host': host,
                            'port': port,
                            'tls_enabled': use_tls
                        },
                        'connection': {
                            'client_id': client_id,
                            'keepalive': keepalive,
                            'clean_session': clean_session,
                            'connect_time_ms': connect_duration
                        },
                        'test': {
                            'topic': test_topic,
                            'subscribe_success': True,
                            'publish_success': True,
                            'message_received': message_received
                        },
                        'protocol_version': 'MQTT 3.1.1' if not use_tls else 'MQTT 3.1.1 over TLS',
                        'on_premise': True
                    },
                    'duration_ms': duration_ms
                }
        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'message': 'Connection timeout (10s)',
                'details': {
                    'error': 'MQTT broker not responding',
                    'host': config.get('host'),
                    'port': config.get('port', 1883),
                    'suggestion': 'Check if MQTT broker is running and port is open'
                },
                'duration_ms': 10000
            }
        
        except ConnectionRefusedError:
            return {
                'success': False,
                'message': 'Connection refused',
                'details': {
                    'error': 'MQTT broker refused connection',
                    'host': config.get('host'),
                    'port': config.get('port', 1883),
                    'suggestion': 'Verify broker is running and accepting connections'
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
        
        except aiomqtt.MqttError as e:
            # Handle authentication errors
            if 'not authorized' in str(e).lower() or 'bad username or password' in str(e).lower():
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'details': {
                        'error': str(e),
                        'username': config.get('username'),
                        'suggestion': 'Check username and password'
                    },
                    'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            return {
                'success': False,
                'message': 'MQTT protocol error',
                'details': {
                    'error': str(e),
                    'type': type(e).__name__
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
        
        except Exception as e:
            logger.error(f"MQTT connection error: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'Connection failed',
                'details': {
                    'error': str(e),
                    'type': type(e).__name__
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
