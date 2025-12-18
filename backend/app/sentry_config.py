# /backend/app/sentry_config.py
"""
Error tracking with Sentry
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import logging

def init_sentry():
    """Initialize Sentry for error tracking"""
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        
        # Integrations
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        
        # Sampling
        traces_sample_rate=0.1,  # Sample 10% of transactions
        profiles_sample_rate=0.01,  # Sample 1% for profiling
        
        # Release tracking
        release=settings.APP_VERSION,
        
        # Filter sensitive data
        before_send=lambda event, hint: filter_sensitive_data(event),
    )

def filter_sensitive_data(event):
    """Remove sensitive data from error events"""
    
    # Remove passwords, tokens, etc.
    if 'request' in event:
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)
    
    if 'exception' in event:
        for exception in event['exception']['values']:
            if 'stacktrace' in exception:
                for frame in exception['stacktrace']['frames']:
                    if 'vars' in frame:
                        frame['vars'].pop('password', None)
                        frame['vars'].pop('token', None)
    
    return event

# Usage
logger = logging.getLogger(__name__)

try:
    process_critical_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.error(f"Critical operation failed: {str(e)}")
