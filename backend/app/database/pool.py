# /backend/app/database/pool.py
"""
Connection pool configuration for production
"""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

def create_engine_with_pool(database_url: str, pool_config: dict):
    """
    Create async engine with optimized connection pool
    
    Pool sizing: pool_size + max_overflow = total connections
    - pool_size: connections kept in pool
    - max_overflow: additional connections for spikes
    """
    
    engine = create_async_engine(
        database_url,
        echo=False,
        
        # Connection pool settings
        poolclass=QueuePool,
        pool_size=pool_config.get("pool_size", 20),
        max_overflow=pool_config.get("max_overflow", 10),
        pool_timeout=pool_config.get("pool_timeout", 30),
        pool_recycle=pool_config.get("pool_recycle", 3600),
        pool_pre_ping=True,  # Test connection before using
        
        # Connection settings
        connect_args={
            "server_settings": {
                "application_name": "cgraph_backend",
                "jit": "off"  # Disable JIT for predictable performance
            },
            "timeout": 10,
            "command_timeout": 10
        }
    )
    
    return engine

# Configuration
POOL_CONFIG = {
    "production": {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600
    },
    "staging": {
        "pool_size": 10,
        "max_overflow": 5,
        "pool_timeout": 30,
        "pool_recycle": 3600
    },
    "development": {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
}
