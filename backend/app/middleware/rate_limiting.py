"""
Comprehensive rate limiting with different rules per endpoint
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379/0"
)

# Rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints - strictest
    "auth_register": "5 per hour",
    "auth_login": "5 per hour",
    "auth_mfa_verify": "10 per hour",
    
    # API endpoints - moderate
    "send_message": "100 per hour",
    "get_messages": "200 per hour",
    "create_room": "20 per hour",
    
    # Payment endpoints - very strict
    "create_payment": "10 per hour",
    "update_subscription": "20 per hour",
    
    # Search - moderate
    "search_messages": "50 per hour",
    "search_users": "50 per hour",
    
    # Upload - strict
    "upload_file": "10 per hour",  # Max 10 files per hour
    
    # General API - loose
    "get_user_profile": "500 per hour",
    "update_profile": "50 per hour",
}

# Apply rate limits to routes
@router.post("/auth/register")
@limiter.limit(RATE_LIMITS["auth_register"])
async def register(request: Request, ...):
    ...

@router.post("/messages/send")
@limiter.limit(RATE_LIMITS["send_message"])
async def send_message(request: Request, ...):
    ...

@router.post("/payments/create")
@limiter.limit(RATE_LIMITS["create_payment"])
async def create_payment(request: Request, ...):
    ...