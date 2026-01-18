"""
RHINOMETRIC API Connector - Kafka Connector
Version: 2.4.0
License: Proprietary

Apache Kafka connector for on-premise event streaming monitoring.
Validates connection, retrieves cluster metadata, and collects key metrics.
"""

import asyncio
from typing import Dict, Any
import logging
from datetime import datetime
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable

logger = logging.getLogger(__name__)


class KafkaConnector:
    """
    Apache Kafka connector using kafka-python library.
    
    Supports:
    - Connection validation
    - Cluster metadata
    - Topic listing
    - Broker information
    - Consumer group status
    
    On-premise philosophy:
    - Validates bootstrap servers are local
    - Warns if cloud endpoints detected
    """
    
    def __init__(self):
        self.name = "Apache Kafka"
        self.version = "2.4.0"
    
    async def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to Kafka cluster.
        
        Args:
            config: {
                'bootstrap_servers': str,  # e.g., 'localhost:9092' or 'kafka1:9092,kafka2:9092'
                'security_protocol': str,  # PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
                'sasl_mechanism': str,     # PLAIN, SCRAM-SHA-256, SCRAM-SHA-512 (if SASL)
                'sasl_username': str,      # Username for SASL
                'sasl_password': str,      # Password for SASL
                'ssl_check_hostname': bool # Verify SSL hostname
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
            bootstrap_servers = config.get('bootstrap_servers', 'localhost:9092')
            security_protocol = config.get('security_protocol', 'PLAINTEXT')
            sasl_mechanism = config.get('sasl_mechanism', 'PLAIN')
            sasl_username = config.get('sasl_username')
            sasl_password = config.get('sasl_password')
            ssl_check_hostname = config.get('ssl_check_hostname', True)
            
            # On-premise validation
            cloud_keywords = ['amazonaws.com', 'azure.com', 'confluent.cloud', 'cloudkarafka.com']
            if any(keyword in bootstrap_servers.lower() for keyword in cloud_keywords):
                logger.warning(f"⚠️ Cloud endpoint detected: {bootstrap_servers}")
                return {
                    'success': False,
                    'message': 'Cloud endpoint detected (RHINOMETRIC is on-premise only)',
                    'details': {
                        'bootstrap_servers': bootstrap_servers,
                        'warning': 'Use local Kafka cluster for on-premise philosophy'
                    },
                    'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            # Build connection config
            admin_config = {
                'bootstrap_servers': bootstrap_servers.split(','),
                'security_protocol': security_protocol,
                'request_timeout_ms': 10000,
                'api_version_auto_timeout_ms': 5000
            }
            
            # Add SASL config if needed
            if security_protocol in ['SASL_PLAINTEXT', 'SASL_SSL']:
                admin_config['sasl_mechanism'] = sasl_mechanism
                admin_config['sasl_plain_username'] = sasl_username
                admin_config['sasl_plain_password'] = sasl_password
            
            # Add SSL config if needed
            if security_protocol in ['SSL', 'SASL_SSL']:
                admin_config['ssl_check_hostname'] = ssl_check_hostname
            
            # Run sync operations in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def connect_kafka():
                try:
                    # Create admin client
                    admin = KafkaAdminClient(**admin_config)
                    
                    # Get cluster metadata
                    cluster_metadata = admin._client.cluster
                    brokers = cluster_metadata.brokers()
                    
                    # Get topics
                    topics = admin.list_topics()
                    
                    # Get consumer groups (expensive, limit to 5s)
                    try:
                        consumer_groups = admin.list_consumer_groups(timeout_ms=5000)
                    except Exception:
                        consumer_groups = []
                    
                    admin.close()
                    
                    return {
                        'brokers': brokers,
                        'topics': topics,
                        'consumer_groups': consumer_groups,
                        'cluster_id': cluster_metadata.cluster_id
                    }
                
                except NoBrokersAvailable as e:
                    raise ConnectionError(f"No brokers available: {e}")
                except KafkaError as e:
                    raise ConnectionError(f"Kafka error: {e}")
            
            # Execute in thread pool
            result = await loop.run_in_executor(None, connect_kafka)
            
            # Extract metrics
            broker_count = len(result['brokers'])
            topic_count = len(result['topics'])
            consumer_group_count = len(result['consumer_groups'])
            
            # Get broker details
            broker_list = []
            for broker in result['brokers']:
                broker_list.append({
                    'id': broker.nodeId,
                    'host': broker.host,
                    'port': broker.port
                })
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'success': True,
                'message': f'Connected to Kafka cluster ({broker_count} brokers)',
                'details': {
                    'cluster_id': result['cluster_id'] or 'unknown',
                    'brokers': {
                        'count': broker_count,
                        'list': broker_list[:3]  # First 3 brokers
                    },
                    'topics': {
                        'count': topic_count,
                        'sample': list(result['topics'])[:5]  # First 5 topics
                    },
                    'consumer_groups': {
                        'count': consumer_group_count
                    },
                    'security_protocol': security_protocol,
                    'on_premise': True
                },
                'duration_ms': duration_ms
            }
        
        except ConnectionError as e:
            return {
                'success': False,
                'message': 'Connection failed',
                'details': {
                    'error': str(e),
                    'bootstrap_servers': config.get('bootstrap_servers'),
                    'suggestion': 'Verify Kafka brokers are running and accessible'
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'message': 'Connection timeout (10s)',
                'details': {
                    'error': 'Kafka cluster not responding',
                    'bootstrap_servers': config.get('bootstrap_servers'),
                    'suggestion': 'Check network connectivity and Kafka listener configuration'
                },
                'duration_ms': 10000
            }
        
        except Exception as e:
            logger.error(f"Kafka connection error: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'Connection failed',
                'details': {
                    'error': str(e),
                    'type': type(e).__name__,
                    'bootstrap_servers': config.get('bootstrap_servers')
                },
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
