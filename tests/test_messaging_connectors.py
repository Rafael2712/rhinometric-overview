"""
RHINOMETRIC v2.4.0 - Messaging Connectors Tests
================================================

Tests unitarios para conectores de messaging:
- RabbitMQ
- Kafka
- MQTT

Filosofía: 100% on-premise, simulación de conexiones locales
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Importar conectores
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../api-connector'))

from connectors.rabbitmq_connector import RabbitMQConnector
from connectors.kafka_connector import KafkaConnector
from connectors.mqtt_connector import MQTTConnector


# =============================================================================
# RABBITMQ TESTS
# =============================================================================

class TestRabbitMQConnector:
    """Tests para RabbitMQ connector."""
    
    @pytest.mark.asyncio
    async def test_rabbitmq_successful_connection(self):
        """Test: Conexión exitosa a RabbitMQ."""
        connector = RabbitMQConnector()
        
        config = {
            'host': 'localhost',
            'port': 15672,
            'username': 'guest',
            'password': 'guest',
            'vhost': '/',
            'use_ssl': False
        }
        
        # Mock aiohttp responses
        mock_overview = {
            'rabbitmq_version': '3.12.0',
            'erlang_version': '25.3',
            'node': 'rabbit@localhost',
            'message_stats': {
                'publish_details': {'rate': 10.5},
                'deliver_details': {'rate': 8.2}
            }
        }
        
        mock_queues = [
            {'messages': 100, 'consumers': 2},
            {'messages': 50, 'consumers': 1}
        ]
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Setup mock
            mock_resp_overview = AsyncMock()
            mock_resp_overview.status = 200
            mock_resp_overview.json = AsyncMock(return_value=mock_overview)
            
            mock_resp_queues = AsyncMock()
            mock_resp_queues.status = 200
            mock_resp_queues.json = AsyncMock(return_value=mock_queues)
            
            mock_session_instance = AsyncMock()
            mock_session_instance.get = AsyncMock()
            mock_session_instance.get.side_effect = [
                AsyncMock(__aenter__=AsyncMock(return_value=mock_resp_overview)),
                AsyncMock(__aenter__=AsyncMock(return_value=mock_resp_queues))
            ]
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is True
        assert 'RabbitMQ' in result['message']
        assert result['details']['rabbitmq_version'] == '3.12.0'
        assert result['details']['queues']['total'] == 2
        assert result['details']['queues']['messages'] == 150
        assert result['details']['on_premise'] is True
        assert result['duration_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_rabbitmq_authentication_failed(self):
        """Test: Error de autenticación en RabbitMQ."""
        connector = RabbitMQConnector()
        
        config = {
            'host': 'localhost',
            'port': 15672,
            'username': 'wrong_user',
            'password': 'wrong_pass',
            'vhost': '/',
            'use_ssl': False
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 401
            
            mock_session_instance = AsyncMock()
            mock_session_instance.get = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp))
            )
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Authentication failed' in result['message']
        assert 'username' in result['details']
    
    @pytest.mark.asyncio
    async def test_rabbitmq_cloud_endpoint_rejection(self):
        """Test: Rechazo de endpoint cloud en RabbitMQ."""
        connector = RabbitMQConnector()
        
        config = {
            'host': 'cloudamqp.com',
            'port': 15672,
            'username': 'user',
            'password': 'pass',
            'vhost': '/',
            'use_ssl': True
        }
        
        result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Cloud endpoint detected' in result['message']
        assert 'on-premise only' in result['message']
        assert result['details']['host'] == 'cloudamqp.com'


# =============================================================================
# KAFKA TESTS
# =============================================================================

class TestKafkaConnector:
    """Tests para Kafka connector."""
    
    @pytest.mark.asyncio
    async def test_kafka_successful_connection(self):
        """Test: Conexión exitosa a Kafka."""
        connector = KafkaConnector()
        
        config = {
            'bootstrap_servers': 'localhost:9092',
            'security_protocol': 'PLAINTEXT',
            'sasl_mechanism': 'PLAIN',
            'sasl_username': None,
            'sasl_password': None,
            'ssl_check_hostname': True
        }
        
        # Mock Kafka admin client
        mock_broker = MagicMock()
        mock_broker.nodeId = 1
        mock_broker.host = 'localhost'
        mock_broker.port = 9092
        
        mock_cluster = MagicMock()
        mock_cluster.brokers.return_value = [mock_broker]
        mock_cluster.cluster_id = 'test-cluster-123'
        
        mock_admin = MagicMock()
        mock_admin._client.cluster = mock_cluster
        mock_admin.list_topics.return_value = ['topic1', 'topic2', 'topic3']
        mock_admin.list_consumer_groups.return_value = [('group1',), ('group2',)]
        mock_admin.close = MagicMock()
        
        with patch('connectors.kafka_connector.KafkaAdminClient', return_value=mock_admin):
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is True
        assert 'Kafka cluster' in result['message']
        assert result['details']['brokers']['count'] == 1
        assert result['details']['topics']['count'] == 3
        assert result['details']['consumer_groups']['count'] == 2
        assert result['details']['on_premise'] is True
        assert result['duration_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_kafka_no_brokers_available(self):
        """Test: Error cuando no hay brokers disponibles."""
        connector = KafkaConnector()
        
        config = {
            'bootstrap_servers': 'localhost:9092',
            'security_protocol': 'PLAINTEXT'
        }
        
        with patch('connectors.kafka_connector.KafkaAdminClient', side_effect=Exception("No brokers available")):
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Connection failed' in result['message']
        assert 'brokers' in result['details']['error'].lower()
    
    @pytest.mark.asyncio
    async def test_kafka_cloud_endpoint_rejection(self):
        """Test: Rechazo de endpoint cloud en Kafka."""
        connector = KafkaConnector()
        
        config = {
            'bootstrap_servers': 'kafka.confluent.cloud:9092',
            'security_protocol': 'SASL_SSL',
            'sasl_mechanism': 'PLAIN',
            'sasl_username': 'user',
            'sasl_password': 'pass'
        }
        
        result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Cloud endpoint detected' in result['message']
        assert 'confluent.cloud' in result['details']['bootstrap_servers']


# =============================================================================
# MQTT TESTS
# =============================================================================

class TestMQTTConnector:
    """Tests para MQTT connector."""
    
    @pytest.mark.asyncio
    async def test_mqtt_successful_connection(self):
        """Test: Conexión exitosa a MQTT."""
        connector = MQTTConnector()
        
        config = {
            'host': 'localhost',
            'port': 1883,
            'username': 'mqtt_user',
            'password': 'mqtt_pass',
            'client_id': 'rhinometric-test',
            'use_tls': False,
            'keepalive': 60,
            'clean_session': True,
            'test_topic': 'test/topic'
        }
        
        # Mock aiomqtt Client
        mock_message = MagicMock()
        mock_message.topic = MagicMock()
        mock_message.topic.matches.return_value = True
        
        mock_client = AsyncMock()
        mock_client.subscribe = AsyncMock()
        mock_client.publish = AsyncMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.__aiter__ = AsyncMock(return_value=iter([mock_message]))
        
        with patch('connectors.mqtt_connector.aiomqtt.Client') as mock_mqtt_class:
            mock_mqtt_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_mqtt_class.return_value.__aexit__ = AsyncMock()
            
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is True
        assert 'MQTT broker' in result['message']
        assert result['details']['broker']['host'] == 'localhost'
        assert result['details']['connection']['client_id'] == 'rhinometric-test'
        assert result['details']['test']['subscribe_success'] is True
        assert result['details']['on_premise'] is True
        assert result['duration_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_mqtt_connection_refused(self):
        """Test: Error de conexión rechazada en MQTT."""
        connector = MQTTConnector()
        
        config = {
            'host': 'localhost',
            'port': 1883,
            'client_id': 'rhinometric-test'
        }
        
        with patch('connectors.mqtt_connector.aiomqtt.Client', side_effect=ConnectionRefusedError("Connection refused")):
            result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Connection refused' in result['message']
        assert 'running' in result['details']['suggestion'].lower()
    
    @pytest.mark.asyncio
    async def test_mqtt_public_broker_rejection(self):
        """Test: Rechazo de broker público en MQTT."""
        connector = MQTTConnector()
        
        config = {
            'host': 'test.mosquitto.org',
            'port': 1883,
            'client_id': 'rhinometric-test'
        }
        
        result = await connector.test_connection(config)
        
        # Assertions
        assert result['success'] is False
        assert 'Public/cloud broker detected' in result['message']
        assert 'on-premise only' in result['message']
        assert 'mosquitto' in result['details']['host'].lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestMessagingIntegration:
    """Tests de integración para los 3 conectores."""
    
    @pytest.mark.asyncio
    async def test_all_connectors_timeout_handling(self):
        """Test: Manejo de timeout en todos los conectores."""
        configs = [
            (RabbitMQConnector(), {'host': '10.255.255.1', 'port': 15672, 'username': 'guest', 'password': 'guest'}),
            (KafkaConnector(), {'bootstrap_servers': '10.255.255.1:9092', 'security_protocol': 'PLAINTEXT'}),
            (MQTTConnector(), {'host': '10.255.255.1', 'port': 1883, 'client_id': 'test'})
        ]
        
        for connector, config in configs:
            # Mock timeout
            with patch.object(connector, 'test_connection', return_value={
                'success': False,
                'message': 'Connection timeout (10s)',
                'details': {'error': 'not responding'},
                'duration_ms': 10000
            }):
                result = await connector.test_connection(config)
                
                assert result['success'] is False
                assert 'timeout' in result['message'].lower()
                assert result['duration_ms'] == 10000
    
    def test_all_connectors_have_version(self):
        """Test: Todos los conectores tienen versión definida."""
        connectors = [
            RabbitMQConnector(),
            KafkaConnector(),
            MQTTConnector()
        ]
        
        for connector in connectors:
            assert hasattr(connector, 'version')
            assert connector.version == '2.4.0'
            assert hasattr(connector, 'name')


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestMessagingPerformance:
    """Tests de performance para conectores de messaging."""
    
    @pytest.mark.asyncio
    async def test_connection_test_duration_under_threshold(self):
        """Test: Duración de test de conexión menor a 15 segundos."""
        connector = RabbitMQConnector()
        
        config = {
            'host': 'localhost',
            'port': 15672,
            'username': 'guest',
            'password': 'guest'
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={
                'rabbitmq_version': '3.12.0',
                'erlang_version': '25.3',
                'node': 'rabbit@localhost',
                'message_stats': {}
            })
            
            mock_session_instance = AsyncMock()
            mock_session_instance.get = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp))
            )
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            start = datetime.now()
            result = await connector.test_connection(config)
            duration = (datetime.now() - start).total_seconds()
        
        # Assertions
        assert duration < 15.0, f"Test took {duration}s (threshold: 15s)"
        assert result['duration_ms'] < 15000


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
