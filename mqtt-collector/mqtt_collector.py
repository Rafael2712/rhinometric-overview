"""
RHINOMETRIC MQTT Collector v1.0
================================

Servicio que se conecta a brokers MQTT públicos para recolectar datos IoT
y exponerlos como métricas de Prometheus para visualización en Grafana.

Broker público utilizado: broker.hivemq.com (más estable que test.mosquitto.org)
Tópicos de ejemplo con datos IoT reales públicos.
"""

import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional
import aiomqtt
from prometheus_client import Counter, Gauge, Histogram, start_http_server, REGISTRY
from collections import defaultdict

# Configuración logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MÉTRICAS PROMETHEUS
# ============================================================================

# Métricas de conexión MQTT
mqtt_connection_status = Gauge(
    'mqtt_connection_status',
    'MQTT broker connection status (1=connected, 0=disconnected)',
    ['broker', 'port']
)

mqtt_messages_received_total = Counter(
    'mqtt_messages_received_total',
    'Total number of MQTT messages received',
    ['topic', 'broker']
)

mqtt_messages_bytes_total = Counter(
    'mqtt_messages_bytes_total',
    'Total bytes received from MQTT messages',
    ['topic', 'broker']
)

mqtt_connection_errors_total = Counter(
    'mqtt_connection_errors_total',
    'Total number of MQTT connection errors',
    ['broker', 'error_type']
)

mqtt_message_processing_time = Histogram(
    'mqtt_message_processing_seconds',
    'Time spent processing MQTT messages',
    ['topic']
)

# Métricas de sensores IoT (dinámicas según los datos recibidos)
iot_sensor_temperature = Gauge(
    'iot_sensor_temperature_celsius',
    'Temperature readings from IoT sensors',
    ['sensor_id', 'location', 'topic']
)

iot_sensor_humidity = Gauge(
    'iot_sensor_humidity_percent',
    'Humidity readings from IoT sensors',
    ['sensor_id', 'location', 'topic']
)

iot_sensor_pressure = Gauge(
    'iot_sensor_pressure_hpa',
    'Pressure readings from IoT sensors',
    ['sensor_id', 'location', 'topic']
)

iot_sensor_light = Gauge(
    'iot_sensor_light_lux',
    'Light level readings from IoT sensors',
    ['sensor_id', 'location', 'topic']
)

iot_device_status = Gauge(
    'iot_device_status',
    'IoT device status (1=online, 0=offline)',
    ['device_id', 'device_type', 'topic']
)

iot_sensor_value = Gauge(
    'iot_sensor_value',
    'Generic sensor value',
    ['sensor_id', 'sensor_type', 'unit', 'topic']
)

# ============================================================================
# MQTT COLLECTOR CLASS
# ============================================================================

class MQTTCollector:
    """
    Recolector de métricas MQTT que se suscribe a tópicos y extrae datos IoT.
    """
    
    def __init__(self, broker: str, port: int = 1883, client_id: str = "rhinometric-collector"):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.running = False
        self.client: Optional[aiomqtt.Client] = None
        self.message_count = defaultdict(int)
        
        # Tópicos públicos con datos IoT reales
        # Usando wildcards específicos para capturar datos interesantes
        self.topics = [
            "owntracks/#",           # Tracking GPS en tiempo real
            "sensor/#",              # Sensores genéricos
            "temperature/#",         # Sensores de temperatura
            "humidity/#",            # Sensores de humedad
            "$SYS/#",                # Estadísticas del broker
            "test/#",                # Tópicos de prueba públicos
            "esp/#",                 # Dispositivos ESP32/ESP8266
            "arduino/#",             # Dispositivos Arduino
            "iot/#",                 # Dispositivos IoT genéricos
        ]
        
        logger.info(f"Inicializando MQTT Collector")
        logger.info(f"  Broker: {self.broker}:{self.port}")
        logger.info(f"  Client ID: {self.client_id}")
        logger.info(f"  Tópicos: {self.topics}")
    
    async def connect(self):
        """Conectar al broker MQTT."""
        try:
            logger.info(f"Conectando a {self.broker}:{self.port}...")
            
            self.client = aiomqtt.Client(
                hostname=self.broker,
                port=self.port,
                identifier=self.client_id,
                keepalive=60,
                clean_session=True,
                timeout=30
            )
            
            await self.client.__aenter__()
            
            # Actualizar métrica de conexión
            mqtt_connection_status.labels(
                broker=self.broker,
                port=self.port
            ).set(1)
            
            logger.info(f"✅ Conectado a {self.broker}:{self.port}")
            
            # Suscribirse a tópicos
            for topic in self.topics:
                await self.client.subscribe(topic)
                logger.info(f"📡 Suscrito a: {topic}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            mqtt_connection_status.labels(
                broker=self.broker,
                port=self.port
            ).set(0)
            mqtt_connection_errors_total.labels(
                broker=self.broker,
                error_type=type(e).__name__
            ).inc()
            return False
    
    def parse_message(self, topic: str, payload: str) -> Optional[Dict[str, Any]]:
        """
        Parsear mensaje MQTT y extraer datos de sensores.
        
        Formatos soportados:
        - JSON: {"temperature": 25.5, "humidity": 60}
        - Texto plano: "25.5"
        - Key-value: "temp=25.5,hum=60"
        """
        try:
            # Intentar parsear como JSON
            try:
                data = json.loads(payload)
                if isinstance(data, dict):
                    return {
                        'format': 'json',
                        'data': data,
                        'raw': payload
                    }
            except json.JSONDecodeError:
                pass
            
            # Intentar parsear como número
            try:
                value = float(payload)
                return {
                    'format': 'numeric',
                    'value': value,
                    'raw': payload
                }
            except ValueError:
                pass
            
            # Intentar parsear como key-value
            if '=' in payload:
                pairs = payload.split(',')
                data = {}
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        try:
                            data[key.strip()] = float(value.strip())
                        except ValueError:
                            data[key.strip()] = value.strip()
                
                if data:
                    return {
                        'format': 'keyvalue',
                        'data': data,
                        'raw': payload
                    }
            
            # Fallback: texto plano
            return {
                'format': 'text',
                'text': payload,
                'raw': payload
            }
            
        except Exception as e:
            logger.warning(f"Error parseando mensaje: {e}")
            return None
    
    def extract_sensor_id(self, topic: str) -> str:
        """Extraer ID del sensor desde el tópico."""
        # Ejemplos:
        # sensors/temp-01/temperature -> temp-01
        # home/livingroom/status -> livingroom
        # devices/sensor-123/data -> sensor-123
        
        parts = topic.split('/')
        if len(parts) >= 2:
            return parts[1]  # Segundo elemento suele ser el ID
        return "unknown"
    
    def extract_location(self, topic: str) -> str:
        """Extraer ubicación desde el tópico."""
        parts = topic.split('/')
        if len(parts) >= 1:
            return parts[0]  # Primer elemento suele ser la ubicación
        return "unknown"
    
    def process_sensor_data(self, topic: str, parsed_data: Dict[str, Any]):
        """Procesar datos de sensores y actualizar métricas Prometheus."""
        try:
            sensor_id = self.extract_sensor_id(topic)
            location = self.extract_location(topic)
            
            if parsed_data['format'] == 'json' and 'data' in parsed_data:
                data = parsed_data['data']
                
                # Temperatura
                if 'temperature' in data or 'temp' in data or 't' in data:
                    temp = data.get('temperature') or data.get('temp') or data.get('t')
                    if temp is not None:
                        try:
                            temp_value = float(temp)
                            iot_sensor_temperature.labels(
                                sensor_id=sensor_id,
                                location=location,
                                topic=topic
                            ).set(temp_value)
                            logger.debug(f"🌡️  Temperatura: {temp_value}°C (sensor: {sensor_id})")
                        except (ValueError, TypeError):
                            pass
                
                # Humedad
                if 'humidity' in data or 'hum' in data or 'h' in data:
                    hum = data.get('humidity') or data.get('hum') or data.get('h')
                    if hum is not None:
                        try:
                            hum_value = float(hum)
                            iot_sensor_humidity.labels(
                                sensor_id=sensor_id,
                                location=location,
                                topic=topic
                            ).set(hum_value)
                            logger.debug(f"💧 Humedad: {hum_value}% (sensor: {sensor_id})")
                        except (ValueError, TypeError):
                            pass
                
                # Presión
                if 'pressure' in data or 'press' in data or 'p' in data:
                    press = data.get('pressure') or data.get('press') or data.get('p')
                    if press is not None:
                        try:
                            press_value = float(press)
                            iot_sensor_pressure.labels(
                                sensor_id=sensor_id,
                                location=location,
                                topic=topic
                            ).set(press_value)
                            logger.debug(f"🌡️  Presión: {press_value} hPa (sensor: {sensor_id})")
                        except (ValueError, TypeError):
                            pass
                
                # Luz
                if 'light' in data or 'lux' in data or 'l' in data:
                    light = data.get('light') or data.get('lux') or data.get('l')
                    if light is not None:
                        try:
                            light_value = float(light)
                            iot_sensor_light.labels(
                                sensor_id=sensor_id,
                                location=location,
                                topic=topic
                            ).set(light_value)
                            logger.debug(f"💡 Luz: {light_value} lux (sensor: {sensor_id})")
                        except (ValueError, TypeError):
                            pass
                
                # Estado del dispositivo
                if 'status' in data or 'state' in data:
                    status = data.get('status') or data.get('state')
                    if status is not None:
                        status_value = 1 if str(status).lower() in ['online', 'on', 'true', '1', 'active'] else 0
                        iot_device_status.labels(
                            device_id=sensor_id,
                            device_type=location,
                            topic=topic
                        ).set(status_value)
                        logger.debug(f"📟 Estado: {'online' if status_value else 'offline'} (device: {sensor_id})")
                
                # Valores genéricos (cualquier otro campo numérico)
                for key, value in data.items():
                    if key not in ['temperature', 'temp', 't', 'humidity', 'hum', 'h', 
                                   'pressure', 'press', 'p', 'light', 'lux', 'l', 'status', 'state']:
                        try:
                            numeric_value = float(value)
                            iot_sensor_value.labels(
                                sensor_id=sensor_id,
                                sensor_type=key,
                                unit='unknown',
                                topic=topic
                            ).set(numeric_value)
                            logger.debug(f"📊 {key}: {numeric_value} (sensor: {sensor_id})")
                        except (ValueError, TypeError):
                            pass
            
            elif parsed_data['format'] == 'numeric':
                # Valor numérico simple
                value = parsed_data['value']
                iot_sensor_value.labels(
                    sensor_id=sensor_id,
                    sensor_type='value',
                    unit='unknown',
                    topic=topic
                ).set(value)
                logger.debug(f"📊 Valor: {value} (sensor: {sensor_id}, topic: {topic})")
            
        except Exception as e:
            logger.warning(f"Error procesando datos del sensor: {e}")
    
    async def process_message(self, message: aiomqtt.Message):
        """Procesar un mensaje MQTT recibido."""
        start_time = datetime.now()
        
        try:
            topic = str(message.topic)
            payload = message.payload.decode('utf-8', errors='ignore')
            
            # Actualizar contadores
            mqtt_messages_received_total.labels(
                topic=topic,
                broker=self.broker
            ).inc()
            
            mqtt_messages_bytes_total.labels(
                topic=topic,
                broker=self.broker
            ).inc(len(message.payload))
            
            self.message_count[topic] += 1
            
            # Parsear mensaje
            parsed_data = self.parse_message(topic, payload)
            
            if parsed_data:
                # Procesar datos de sensores
                self.process_sensor_data(topic, parsed_data)
                
                # Log de mensaje recibido (limitado para evitar spam)
                if self.message_count[topic] % 10 == 1:  # Log cada 10 mensajes
                    logger.info(f"📨 Mensaje #{self.message_count[topic]} - Topic: {topic}")
                    logger.info(f"   Formato: {parsed_data['format']}")
                    if len(payload) < 200:
                        logger.info(f"   Payload: {payload}")
            
            # Métrica de tiempo de procesamiento
            duration = (datetime.now() - start_time).total_seconds()
            mqtt_message_processing_time.labels(topic=topic).observe(duration)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
    
    async def run(self):
        """Ejecutar el recolector MQTT."""
        self.running = True
        
        while self.running:
            try:
                # Conectar al broker
                if not await self.connect():
                    logger.warning("Reintentando conexión en 10 segundos...")
                    await asyncio.sleep(10)
                    continue
                
                # Procesar mensajes
                logger.info("🎧 Escuchando mensajes MQTT...")
                
                async for message in self.client.messages:
                    await self.process_message(message)
                
            except aiomqtt.MqttError as e:
                logger.error(f"Error MQTT: {e}")
                mqtt_connection_status.labels(
                    broker=self.broker,
                    port=self.port
                ).set(0)
                mqtt_connection_errors_total.labels(
                    broker=self.broker,
                    error_type=type(e).__name__
                ).inc()
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Deteniendo recolector...")
                self.running = False
                break
                
            except Exception as e:
                logger.error(f"Error inesperado: {e}", exc_info=True)
                await asyncio.sleep(5)
        
        # Cleanup
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except:
                pass
        
        mqtt_connection_status.labels(
            broker=self.broker,
            port=self.port
        ).set(0)
        
        logger.info("Recolector detenido")
    
    def stop(self):
        """Detener el recolector."""
        self.running = False


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Función principal."""
    
    # Iniciar servidor HTTP de métricas Prometheus
    metrics_port = 9300
    logger.info(f"🚀 Iniciando servidor de métricas en puerto {metrics_port}")
    start_http_server(metrics_port)
    logger.info(f"📊 Métricas disponibles en http://localhost:{metrics_port}/metrics")
    
    # Broker MQTT público con datos IoT reales
    # broker.hivemq.com es más estable y tiene muchos dispositivos IoT públicos
    broker = "broker.hivemq.com"
    port = 1883
    
    logger.info("=" * 70)
    logger.info("RHINOMETRIC MQTT Collector v1.0")
    logger.info("=" * 70)
    logger.info(f"Broker: {broker}:{port}")
    logger.info(f"Métricas: http://localhost:{metrics_port}/metrics")
    logger.info("=" * 70)
    
    # Crear y ejecutar recolector
    collector = MQTTCollector(broker=broker, port=port)
    
    try:
        await collector.run()
    except KeyboardInterrupt:
        logger.info("Cerrando aplicación...")
        collector.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Aplicación terminada")

