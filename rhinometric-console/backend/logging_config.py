"""
JSON Structured Logging Configuration for Rhinometric Console Backend
Provides correlation-ready logs with trace_id, span_id, and full context
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context vars for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar('span_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Correlates with OpenTelemetry traces and Prometheus metrics
    """
    
    def __init__(self, service_name: str = "console-backend"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log structure
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_obj["request_id"] = request_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            log_obj["trace_id"] = trace_id
        
        span_id = span_id_var.get()
        if span_id:
            log_obj["span_id"] = span_id
        
        user_id = user_id_var.get()
        if user_id:
            log_obj["user_id"] = user_id
        
        # Add custom fields from extra
        if hasattr(record, 'endpoint'):
            log_obj["endpoint"] = record.endpoint
        
        if hasattr(record, 'method'):
            log_obj["method"] = record.method
        
        if hasattr(record, 'status_code'):
            log_obj["status_code"] = record.status_code
        
        if hasattr(record, 'duration_ms'):
            log_obj["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'error_code'):
            log_obj["error_code"] = record.error_code
        
        if hasattr(record, 'db_query'):
            log_obj["db_query"] = record.db_query
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add source location
        log_obj["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        return json.dumps(log_obj)


def setup_json_logging(service_name: str = "console-backend", log_level: str = "INFO"):
    """
    Configure root logger with JSON formatter
    
    Args:
        service_name: Name of the service for log correlation
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Create JSON formatter
    json_formatter = JSONFormatter(service_name=service_name)
    
    # Configure stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(json_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers and add JSON handler
    root_logger.handlers = []
    root_logger.addHandler(stdout_handler)
    
    # Configure specific loggers
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("JSON structured logging initialized", extra={
        "service": service_name,
        "log_level": log_level
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with JSON formatting
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Helper functions for context management
def set_request_context(
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Set request-scoped context variables for logging correlation"""
    if request_id:
        request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)
    if span_id:
        span_id_var.set(span_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request-scoped context variables"""
    request_id_var.set(None)
    trace_id_var.set(None)
    span_id_var.set(None)
    user_id_var.set(None)


def log_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    **kwargs
):
    """
    Log HTTP request with structured data
    
    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional fields (user_id, error_code, etc.)
    """
    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    level = logging.INFO
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    
    logger.log(level, f"{method} {endpoint} {status_code} ({duration_ms:.2f}ms)", extra=extra)


def log_db_query(
    logger: logging.Logger,
    query_type: str,
    duration_ms: float,
    error: Optional[str] = None,
    **kwargs
):
    """
    Log database query with structured data
    
    Args:
        logger: Logger instance
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        duration_ms: Query duration in milliseconds
        error: Error message if query failed
        **kwargs: Additional fields (table, rows_affected, etc.)
    """
    extra = {
        "query_type": query_type,
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    if error:
        extra["error_code"] = "DB_QUERY_ERROR"
        logger.error(f"DB query failed: {error}", extra=extra)
    elif duration_ms > 1000:
        logger.warning(f"Slow DB query: {query_type} ({duration_ms:.2f}ms)", extra=extra)
    else:
        logger.debug(f"DB query: {query_type} ({duration_ms:.2f}ms)", extra=extra)
