# /backend/app/logging_config.py
"""
Structured logging with JSON output for log aggregation
"""

import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
import sys

def setup_logging():
    """
    Configure structured logging
    Outputs JSON to stdout for log aggregation (CloudWatch, ELK)
    """
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        timestamp=True,
        rename_fields={"timestamp": "@timestamp"}
    )
    
    # Stdout handler (for CloudWatch, ELK)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(json_formatter)
    logger.addHandler(stdout_handler)
    
    # Return logger
    return logger

logger = setup_logging()

# Structured logging examples
def log_request(request, execution_time_ms: float, status_code: int):
    """Log API request"""
    
    logger.info(
        "API request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "execution_time_ms": execution_time_ms,
            "user_id": getattr(request.state, "user_id", None),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent")
        }
    )

def log_database_query(query: str, execution_time_ms: float, rows_affected: int):
    """Log database query"""
    
    logger.debug(
        "Database query executed",
        extra={
            "query": query,
            "execution_time_ms": execution_time_ms,
            "rows_affected": rows_affected
        }
    )

def log_error(error_code: str, message: str, context: dict = None):
    """Log error"""
    
    logger.error(
        message,
        extra={
            "error_code": error_code,
            **context or {}
        },
        exc_info=True
    )
