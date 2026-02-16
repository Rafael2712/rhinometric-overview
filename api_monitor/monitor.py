"""
Cliente para la API del Ayuntamiento de Madrid con manejo de errores y métricas
"""

import requests
import logging
import time
import os
import signal
import sys
from datetime import datetime
import json
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configurar logging básico primero
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from config.api_config import API_CONFIG, MONITOR_CONFIG, METRICS
    logging.info("Configuración cargada correctamente")
except ImportError as e:
    logging.error(f"Error al cargar la configuración: {e}")
    raise

class APIMonitor:
    def __init__(self):
        self.session = self._create_session()
        self.cache = {}
        self.logger = self._setup_logger()
        self.running = True
        self.last_error = None
        self.last_success = time.time()
        self.setup_signal_handlers()
        self.executor = ThreadPoolExecutor(max_workers=MONITOR_CONFIG.get('batch_size', 2))
        self.start_health_server()

    def setup_signal_handlers(self):
        """Configura los manejadores de señales para un cierre limpio"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Maneja el cierre limpio del monitor"""
        self.logger.info("Recibida señal de apagado. Cerrando el monitor...")
        self.running = False
        if hasattr(self, 'health_server'):
            self.health_server.shutdown()
        self.executor.shutdown(wait=True)
        sys.exit(0)

    def health_check_handler(self):
        """Manejador para el endpoint de health check"""
        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self_handler):
                if self_handler.path == '/health':
                    # Verificar si el monitor está funcionando correctamente
                    time_since_last_success = time.time() - self.last_success
                    if time_since_last_success > MONITOR_CONFIG['health_check'].get('max_failure_time', 300):
                        self_handler.send_response(503)
                        self_handler.send_header('Content-type', 'application/json')
                        self_handler.end_headers()
                        status = {
                            'status': 'error',
                            'last_error': str(self.last_error),
                            'time_since_success': time_since_last_success
                        }
                    else:
                        self_handler.send_response(200)
                        self_handler.send_header('Content-type', 'application/json')
                        self_handler.end_headers()
                        status = {
                            'status': 'healthy',
                            'last_success': self.last_success,
                            'uptime': time.time() - self.start_time
                        }
                    self_handler.wfile.write(json.dumps(status).encode())
                else:
                    self_handler.send_response(404)
                    self_handler.end_headers()
            
            def log_message(self, format, *args):
                # Suprimir logs de acceso HTTP
                pass
        
        return HealthCheckHandler

    def start_health_server(self):
        """Inicia el servidor de health check en un thread separado"""
        if MONITOR_CONFIG['health_check']['enabled']:
            self.start_time = time.time()
            server_address = ('', 8000)
            self.health_server = HTTPServer(server_address, self.health_check_handler())
            health_thread = threading.Thread(target=self.health_server.serve_forever)
            health_thread.daemon = True
            health_thread.start()
            self.logger.info("Servidor de health check iniciado en puerto 8000")

    def _create_session(self) -> requests.Session:
        """Configura una sesión de requests con retry y timeouts"""
        session = requests.Session()
        retry_strategy = Retry(
            total=MONITOR_CONFIG['retry']['max_attempts'],
            backoff_factor=MONITOR_CONFIG['retry']['backoff_factor'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=MONITOR_CONFIG.get('batch_size', 2),
            pool_maxsize=MONITOR_CONFIG.get('batch_size', 2)
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _setup_logger(self) -> logging.Logger:
        """Configura el logger para el monitoreo"""
        logger = logging.getLogger('api_monitor')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/app/logs/ayuntamiento.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _check_cache(self, endpoint: str) -> Optional[Dict]:
        """Verifica si hay datos en caché y si son válidos"""
        if not MONITOR_CONFIG['cache']['enabled']:
            return None
        
        cache_data = self.cache.get(endpoint)
        if cache_data is None:
            return None

        cache_time, data = cache_data
        age = time.time() - cache_time
        if age < MONITOR_CONFIG['cache']['duration']:
            self.logger.debug(f"Usando datos en caché para {endpoint}, edad: {age}s")
            return data
        return None

    def _validate_data_quality(self, data: Any) -> bool:
        """Valida la calidad de los datos de AEMET"""
        if data is None:
            return False

        # Para arrays (como en observaciones)
        if isinstance(data, list):
            return len(data) > 0

        # Para objetos individuales
        if isinstance(data, dict):
            # Verificar que tenga al menos algunos campos comunes de AEMET
            common_fields = ['fecha', 'estado', 'datos', 'metadatos']
            return any(field in data for field in common_fields)

        return False

    def _check_data_freshness(self, data: Dict) -> bool:
        """Verifica la frescura de los datos"""
        if not METRICS['data_freshness']['enabled']:
            return True

        try:
            fecha_str = data.get('fecha_actualizacion')
            if not fecha_str:
                return False

            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            age = (datetime.now() - fecha).total_seconds()
            
            if age > METRICS['data_freshness']['max_age']:
                self.logger.warning(f"Datos demasiado antiguos: {age}s")
                return False
            return True
        except (ValueError, TypeError):
            self.logger.error("Error al verificar la frescura de los datos")
            return False

    def fetch_data(self, endpoint_key: str) -> Dict[str, Any]:
        """Obtiene datos de un endpoint específico con manejo de caché y validación"""
        endpoint = API_CONFIG['endpoints'].get(endpoint_key)
        if not endpoint:
            raise ValueError(f"Endpoint no configurado: {endpoint_key}")

        # Verificar caché
        cached_data = self._check_cache(endpoint)
        if cached_data:
            return cached_data

        url = f"{API_CONFIG['base_url']}{endpoint}"
        start_time = time.time()

        try:
            # Primera petición para obtener la URL de los datos
            headers = {'api_key': API_CONFIG['api_key']}
            response = self.session.get(
                url,
                headers=headers,
                timeout=API_CONFIG['timeout']
            )
            response.raise_for_status()
            metadata = response.json()

            if 'datos' not in metadata:
                raise ValueError(f"La respuesta de AEMET no contiene la URL de datos para {endpoint_key}")

            # Segunda petición para obtener los datos reales
            data_response = self.session.get(
                metadata['datos'],
                timeout=API_CONFIG['timeout']
            )
            data_response.raise_for_status()
            data = data_response.json()

            latency = time.time() - start_time
            
            # Registrar latencia
            self.logger.info(f"Latencia API {endpoint_key}: {latency:.2f}s")
            if latency > METRICS['response_time']['threshold_warning']:
                self.logger.warning(f"Latencia alta en {endpoint_key}: {latency:.2f}s")

            # Validar calidad y frescura
            if not self._validate_data_quality(data):
                self.logger.error(f"Datos no válidos de {endpoint_key}")
                return {'error': 'Datos no válidos'}

            if not self._check_data_freshness(data):
                self.logger.warning(f"Datos no actualizados de {endpoint_key}")

            # Actualizar caché
            if MONITOR_CONFIG['cache']['enabled']:
                self.cache[endpoint] = (time.time(), data)

            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al consultar {endpoint_key}: {str(e)}")
            return {'error': str(e)}

    def monitor(self):
        """Función principal de monitoreo"""
        self.logger.info("Iniciando el monitor de APIs del Ayuntamiento de Madrid")
        
        while self.running:
            try:
                # Crear futures para todas las peticiones
                futures_to_endpoints = {
                    self.executor.submit(self.fetch_data, endpoint_key): endpoint_key
                    for endpoint_key in API_CONFIG['endpoints']
                }

                # Esperar a que todas las peticiones terminen o hasta que expire el timeout
                for future in as_completed(futures_to_endpoints, timeout=MONITOR_CONFIG.get('batch_timeout', 30)):
                    endpoint_key = futures_to_endpoints[future]
                    try:
                        data = future.result()
                        self.logger.info(f"Datos obtenidos de {endpoint_key}: {len(str(data))} bytes")
                    except Exception as e:
                        self.logger.error(f"Error en monitoreo de {endpoint_key}: {str(e)}")

            except TimeoutError:
                self.logger.error("Timeout en el procesamiento por lotes de endpoints")
            except Exception as e:
                self.logger.error(f"Error general en el ciclo de monitoreo: {str(e)}")
            
            # Solo dormir si aún estamos ejecutando
            if self.running:
                time.sleep(MONITOR_CONFIG['interval'])

if __name__ == "__main__":
    monitor = APIMonitor()
    monitor.monitor()