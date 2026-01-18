"""
RHINOMETRIC v2.5.0 - Database Collector Template
=================================================

Auto-generated database collector for SQL monitoring.

Configuration variables (injected by system):
- DB_TYPE: postgresql
- DB_HOST: rhinometric-postgres
- DB_PORT: 5432
- DB_NAME: rhinometric
- DB_USER: rhinometric
- DB_PASSWORD: rhinometric_demo
- METRICS_PORT: 9342
- QUERY_INTERVAL: 60
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from datetime import datetime
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import os

# ============================================================================
# OPENTELEMETRY CONFIGURATION
# ============================================================================

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": f"database-collector-default",
    "deployment.environment": "production",
    "service.version": "2.5.0",
    "db.type": "postgresql"
})

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
    insecure=True
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# ============================================================================
# CONFIGURATION (auto-injected)
# ============================================================================

DB_TYPE = os.getenv("DB_TYPE", "postgresql")  # postgresql, mysql, mongodb
DB_HOST = os.getenv("DB_HOST", "rhinometric-postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "rhinometric")
DB_USER = os.getenv("DB_USER", "rhinometric")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rhinometric_demo")
QUERY_SQL = os.getenv("QUERY_SQL", """SELECT 1 as test""")
METRICS_PORT = int(os.getenv("METRICS_PORT", "9342"))
QUERY_INTERVAL = int(os.getenv("QUERY_INTERVAL", "60"))

# Connection settings
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "10"))  # seconds
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "30"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # seconds

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Connection status
db_connection_status = Gauge(
    'db_connection_status',
    'Database connection status (1=connected, 0=disconnected)'
)

# Query counters
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries executed',
    ['query_type', 'status']
)

# Connection pool
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections'
)

# Query performance
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query execution time in seconds',
    ['query_type']
)

# Records fetched
db_records_fetched_total = Counter(
    'db_records_fetched_total',
    'Total records fetched from database'
)

db_records_current = Gauge(
    'db_records_current',
    'Current number of records in result set'
)

# Last successful query
db_last_success_timestamp = Gauge(
    'db_last_success_timestamp',
    'Timestamp of last successful query'
)

# ============================================================================
# DATABASE ENGINE
# ============================================================================

def create_db_engine():
    """
    Create SQLAlchemy engine based on database type.
    """
    try:
        if DB_TYPE == "postgresql":
            connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout={CONNECTION_TIMEOUT}"
        elif DB_TYPE == "mysql":
            connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout={CONNECTION_TIMEOUT}"
        elif DB_TYPE == "mongodb":
            connection_string = f"mongodb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?serverSelectionTimeoutMS={CONNECTION_TIMEOUT * 1000}"
        else:
            raise ValueError(f"Unsupported database type: {DB_TYPE}")
        
        logger.info(f"🔗 Connecting to {DB_TYPE}://{DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False  # Set to True for SQL debugging
        )
        
        # Test connection immediately
        with engine.connect() as conn:
            logger.info(f"✅ Successfully connected to {DB_TYPE} database")
        
        return engine
    
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        raise
    
    # Instrument SQLAlchemy with OpenTelemetry
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        service=f"database-collector-default"
    )
    
    return engine

# ============================================================================
# QUERY EXECUTOR
# ============================================================================

async def execute_queries():
    """
    Execute database queries periodically and collect metrics.
    """
    logger.info(f"🚀 Database Collector started")
    logger.info(f"🗄️  Database: {DB_TYPE}://{DB_HOST}:{DB_PORT}/{DB_NAME}")
    logger.info(f"📊 Metrics exposed on port {METRICS_PORT}")
    logger.info(f"⏱️  Query interval: {QUERY_INTERVAL}s")
    logger.info(f"🔒 Connection timeout: {CONNECTION_TIMEOUT}s, Query timeout: {QUERY_TIMEOUT}s")
    logger.info(f"🔄 Max retries: {MAX_RETRIES}, Retry delay: {RETRY_DELAY}s")
    
    engine = None
    retry_count = 0
    
    # Retry connection with exponential backoff
    while retry_count < MAX_RETRIES:
        try:
            engine = create_db_engine()
            logger.info(f"✅ Database engine created successfully")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Failed to create database engine (attempt {retry_count}/{MAX_RETRIES}): {e}")
            db_connection_status.set(0)
            
            if retry_count < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (retry_count - 1))  # Exponential backoff
                logger.info(f"⏳ Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Max retries reached. Exiting...")
                return
    
    while True:
        # Create OTEL span for database operation
        with tracer.start_as_current_span("db_query_execution") as span:
            try:
                # Add DB attributes to span
                span.set_attribute("db.system", DB_TYPE)
                span.set_attribute("db.name", DB_NAME)
                span.set_attribute("db.user", DB_USER)
                span.set_attribute("db.connection_string", f"{DB_TYPE}://{DB_HOST}:{DB_PORT}/{DB_NAME}")
                
                # Test connection
                with engine.connect() as conn:
                    db_connection_status.set(1)
                    span.set_attribute("db.connection_status", "connected")
                    
                    # Get pool stats
                    pool = engine.pool
                    active_connections = pool.checkedout()
                    idle_connections = pool.size() - pool.checkedout()
                    
                    db_connections_active.set(active_connections)
                    db_connections_idle.set(idle_connections)
                    
                    span.set_attribute("db.pool.active", active_connections)
                    span.set_attribute("db.pool.idle", idle_connections)
                    
                    # Execute query with timing
                    start_time = datetime.now()
                    
                    with tracer.start_as_current_span("db_query") as query_span:
                        query_span.set_attribute("db.statement", QUERY_SQL[:200])  # Truncate for safety
                        query_span.set_attribute("db.operation", "select")
                        
                        result = conn.execute(text(QUERY_SQL))
                        rows = result.fetchall()
                        
                        duration = (datetime.now() - start_time).total_seconds()
                        record_count = len(rows)
                        
                        query_span.set_attribute("db.rows_affected", record_count)
                        query_span.set_attribute("db.duration", duration)
                        query_span.set_attribute("db.status", "success")
                    
                    # Update metrics
                    db_queries_total.labels(
                        query_type='select',
                        status='success'
                    ).inc()
                    
                    db_query_duration_seconds.labels(
                        query_type='select'
                    ).observe(duration)
                    
                    db_records_fetched_total.inc(record_count)
                    db_records_current.set(record_count)
                    db_last_success_timestamp.set(datetime.now().timestamp())
                    
                    span.set_attribute("db.status", "success")
                    logger.info(f"✅ Query executed: {record_count} records in {duration:.3f}s")
                    
            except Exception as e:
                span.set_attribute("db.status", "error")
                span.set_attribute("db.error", str(e))
                logger.error(f"❌ Query error: {e}")
                db_connection_status.set(0)
                db_queries_total.labels(
                    query_type='select',
                    status='error'
                ).inc()
        
        # Wait before next query
        await asyncio.sleep(QUERY_INTERVAL)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    logger.info(f"📊 Prometheus metrics server started on port {METRICS_PORT}")
    
    # Start query executor
    try:
        asyncio.run(execute_queries())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down database collector...")
        db_connection_status.set(0)