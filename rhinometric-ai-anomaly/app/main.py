"""
Main Entry Point
Starts FastAPI server with background detection service
"""
import sys
import logging
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import config_manager
from app.api import app as fastapi_app, detector
from app.service import DetectionService

# ═══════════════════════════════════════════════════════════
# RHINOMETRIC v2.5.0 - OpenTelemetry Auto-Instrumentation
# ═══════════════════════════════════════════════════════════
try:
    from tracing import setup_tracing
    tracer, fastapi_instrumentor = setup_tracing("rhinometric-ai-anomaly")
    # Instrument FastAPI app
    fastapi_instrumentor.instrument_app(fastapi_app)
    print("✓ FastAPI app instrumented for distributed tracing")
except ImportError:
    print("⚠ OpenTelemetry not available - tracing disabled")
    tracer = None
    fastapi_instrumentor = None
except Exception as e:
    print(f"⚠ Failed to instrument FastAPI: {e}")
# ═══════════════════════════════════════════════════════════

# Configure logging
def setup_logging():
    """Setup structured logging"""
    log_config = config_manager.config.logging
    
    # Set log level
    log_level = getattr(logging, log_config.level.upper(), logging.INFO)
    
    # Configure format
    if log_config.format == "json":
        logging.basicConfig(
            level=log_level,
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Set library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# Background service instance
detection_service = None


# Register shutdown event for cleanup
@fastapi_app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global detection_service
    
    logger.info("Shutting down services...")
    
    if detection_service:
        await detection_service.stop()
    
    logger.info("✓ All services stopped")


# Note: FastAPI app already has @app.on_event("startup") in api.py
# We'll add our services there instead


def main():
    """Main entry point"""
    try:
        # Setup logging
        setup_logging()
        
        # Get server config
        server_config = config_manager.config.server
        
        # Run server
        uvicorn.run(
            "app.main:fastapi_app",
            host=server_config.host,
            port=server_config.port,
            workers=1,  # Must be 1 for background tasks
            log_level=server_config.log_level.lower(),
            access_log=False
        )
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
