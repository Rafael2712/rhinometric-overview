#!/usr/bin/env python3
import time
import psycopg2
from prometheus_client import start_http_server, Gauge, Counter
from typing import Dict, Any
import os

# Métricas de Prometheus
POOL_METRICS = {
    'cl_active': Gauge('pgbouncer_pools_client_active_connections', 'Active client connections', ['database']),
    'cl_waiting': Gauge('pgbouncer_pools_client_waiting_connections', 'Waiting client connections', ['database']),
    'sv_active': Gauge('pgbouncer_pools_server_active_connections', 'Active server connections', ['database']),
    'sv_idle': Gauge('pgbouncer_pools_server_idle_connections', 'Idle server connections', ['database']),
    'sv_used': Gauge('pgbouncer_pools_server_used_connections', 'Used server connections', ['database']),
    'maxwait': Gauge('pgbouncer_pools_max_wait_seconds', 'Maximum wait time', ['database'])
}

STATS_METRICS = {
    'total_requests': Counter('pgbouncer_stats_requests_total', 'Total number of requests', ['database']),
    'total_received': Counter('pgbouncer_stats_received_bytes_total', 'Total bytes received', ['database']),
    'total_sent': Counter('pgbouncer_stats_sent_bytes_total', 'Total bytes sent', ['database']),
    'total_query_time': Counter('pgbouncer_stats_query_time_seconds_total', 'Total query time in seconds', ['database']),
    'avg_req': Gauge('pgbouncer_stats_avg_requests', 'Average requests per second', ['database']),
    'avg_recv': Gauge('pgbouncer_stats_avg_receive_bytes', 'Average bytes received per second', ['database']),
    'avg_sent': Gauge('pgbouncer_stats_avg_sent_bytes', 'Average bytes sent per second', ['database']),
    'avg_query': Gauge('pgbouncer_stats_avg_query_seconds', 'Average query time in seconds', ['database'])
}

class PgBouncerExporter:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('PGBOUNCER_HOST', 'pgbouncer'),
            'port': int(os.getenv('PGBOUNCER_PORT', '6432')),
            'user': os.getenv('PGBOUNCER_USER', 'admin'),
            'password': os.getenv('PGBOUNCER_PASSWORD', 'secure_password_123'),
            'database': 'pgbouncer'
        }

    def connect(self) -> psycopg2.extensions.connection:
        print(f"\nAttempting to connect to PgBouncer...")
        print(f"Host: {self.connection_params['host']}")
        print(f"Port: {self.connection_params['port']}")
        print(f"User: {self.connection_params['user']}")
        print(f"Database: {self.connection_params['database']}")
        try:
            print("Establishing connection...")
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = True  # Deshabilitar transacciones automáticas
            print("Successfully established connection to PgBouncer")
            
            # Verificar que realmente podemos ejecutar consultas
            with conn.cursor() as cur:
                print("Testing connection with SHOW VERSION query...")
                cur.execute('SHOW VERSION')
                version = cur.fetchone()[0]
                print(f"PgBouncer version: {version}")
            
            return conn
        except Exception as e:
            print(f"\n!!! Error connecting to PgBouncer !!!")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("Full error details:", e)
            raise

    def execute_show_command(self, command):
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(command)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, record)) for record in cur.fetchall()]
        finally:
            conn.close()

    def get_pools(self) -> None:
        try:
            pools_data = self.execute_show_command('SHOW POOLS')
            for pool_data in pools_data:
                database = pool_data['database']
                for metric_name, metric in POOL_METRICS.items():
                    if metric_name in pool_data:
                        value = pool_data[metric_name]
                        if value is not None:
                            if metric_name == 'maxwait':
                                value = float(value) / 1000000  # Convertir a segundos
                            metric.labels(database=database).set(value)
        except Exception as e:
            print(f"Error collecting pool metrics: {e}")

    def get_stats(self) -> None:
        try:
            stats_data = self.execute_show_command('SHOW STATS')
            for stat in stats_data:
                database = stat['database']
                for metric_name, metric in STATS_METRICS.items():
                    if metric_name in stat:
                        value = stat[metric_name]
                        if value is not None:
                            if 'time' in metric_name:
                                value = float(value) / 1000000  # Convertir a segundos
                            metric.labels(database=database)._value.set(value)
        except Exception as e:
            print(f"Error collecting stats metrics: {e}")

    def collect_metrics(self) -> None:
        """Recolecta todas las métricas de PgBouncer"""
        print("\n--- Starting metrics collection ---")
        try:
            print("Collecting pool metrics...")
            self.get_pools()
            print("Pool metrics collected successfully")
            
            print("Collecting stats metrics...")
            self.get_stats()
            print("Stats metrics collected successfully")
            
            print("Metrics collection completed successfully")
        except Exception as e:
            print(f"Error during metrics collection: {str(e)}")
        print("--- Metrics collection cycle ended ---\n")

def main():
    try:
        print("\n=== Starting PgBouncer Exporter ===")
        # Mostrar variables de entorno
        env_vars = {
            'PGBOUNCER_HOST': os.getenv('PGBOUNCER_HOST', 'pgbouncer'),
            'PGBOUNCER_PORT': os.getenv('PGBOUNCER_PORT', '6432'),
            'PGBOUNCER_USER': os.getenv('PGBOUNCER_USER', 'admin'),
            'PGBOUNCER_PASSWORD': '***********',  # Ocultamos la contraseña
            'EXPORTER_PORT': os.getenv('EXPORTER_PORT', '9127'),
            'COLLECTION_INTERVAL': os.getenv('COLLECTION_INTERVAL', '15')
        }
        print("Environment configuration:")
        for key, value in env_vars.items():
            print(f"  {key}: {value}")
            
        exporter_port = int(env_vars['EXPORTER_PORT'])
        collection_interval = int(env_vars['COLLECTION_INTERVAL'])
        
        print(f"\nStarting HTTP server on port {exporter_port}...")
        start_http_server(exporter_port)
        print("HTTP server started successfully")
        
        print("\nInitializing PgBouncer exporter...")
        exporter = PgBouncerExporter()
        print("PgBouncer exporter initialized successfully")
        
        print("\nStarting metrics collection loop...")
        while True:
            try:
                exporter.collect_metrics()
            except Exception as e:
                print(f"Error during metrics collection cycle: {str(e)}")
                print("Will retry in next cycle")
            
            print(f"\nWaiting {collection_interval} seconds until next collection cycle...")
            time.sleep(collection_interval)
    except Exception as e:
        print(f"Fatal error in exporter: {e}")
        raise

if __name__ == '__main__':
    main()