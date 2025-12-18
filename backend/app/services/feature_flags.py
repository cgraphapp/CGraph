# /backend/app/services/feature_flags.py
"""
Feature flag service for progressive rollout
Supports A/B testing and gradual deployment
"""

import json
import hashlib
from typing import Dict, Optional
from datetime import datetime
import redis.asyncio as redis
from app.config import settings

class FeatureFlags:
    
    # Feature definitions
    FEATURES = {
        'end_to_end_encryption': {
            'enabled': True,
            'rollout_percentage': 100,  # 100% of users
            'description': 'Enable E2E encryption for all messages'
        },
        
        'dark_mode': {
            'enabled': True,
            'rollout_percentage': 50,  # A/B test: 50% of users
            'description': 'Dark mode UI'
        },
        
        'reactions': {
            'enabled': True,
            'rollout_percentage': 75,
            'description': 'Message reactions with emojis'
        },
        
        'voice_messages': {
            'enabled': False,
            'rollout_percentage': 0,
            'description': 'Voice message recording',
            'rollout_date': '2025-02-01'
        },
        
        'video_calls': {
            'enabled': False,
            'rollout_percentage': 0,
            'description': 'Direct video calling',
            'rollout_date': '2025-03-01'
        }
    }
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def is_enabled(
        self,
        feature: str,
        user_id: str,
        force_enable: Optional[bool] = None
    ) -> bool:
        """
        Check if feature is enabled for user
        Uses user ID for consistent A/B assignment
        """
        
        # Check Redis cache first (60s TTL)
        cache_key = f"feature_flag:{feature}:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return cached == b'1'
        
        # Force enable for testing
        if force_enable is not None:
            await self.redis.setex(cache_key, 60, 1 if force_enable else 0)
            return force_enable
        
        # Get feature definition
        feature_def = self.FEATURES.get(feature)
        if not feature_def:
            return False
        
        # Check if globally enabled
        if not feature_def['enabled']:
            await self.redis.setex(cache_key, 60, 0)
            return False
        
        # Check rollout percentage (consistent hash per user)
        rollout_percentage = feature_def.get('rollout_percentage', 0)
        if rollout_percentage == 100:
            result = True
        elif rollout_percentage == 0:
            result = False
        else:
            # Deterministic hash-based assignment
            hash_input = f"{feature}:{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            user_bucket = hash_value % 100
            result = user_bucket < rollout_percentage
        
        # Cache result
        await self.redis.setex(cache_key, 60, 1 if result else 0)
        
        return result
    
    async def get_ab_variant(
        self,
        experiment: str,
        user_id: str
    ) -> str:
        """
        Get A/B test variant for user
        Returns 'control' or 'variant'
        """
        
        hash_input = f"{experiment}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # 50/50 split
        if hash_value % 2 == 0:
            return 'control'
        else:
            return 'variant'
    
    async def track_usage(
        self,
        feature: str,
        user_id: str,
        enabled: bool
    ):
        """Track feature flag usage for analytics"""
        
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'feature': feature,
            'user_id': user_id,
            'enabled': enabled
        }
        
        # Publish to analytics stream
        await self.redis.xadd('feature_usage', event)

# Usage in API
@router.get("/api/v1/features")
async def get_enabled_features(
    current_user: str = Depends(get_current_user),
    flags: FeatureFlags = Depends(get_feature_flags)
):
    """Get list of enabled features for user"""
    
    enabled_features = {}
    
    for feature_name in FeatureFlags.FEATURES.keys():
        is_enabled = await flags.is_enabled(feature_name, current_user)
        enabled_features[feature_name] = is_enabled
        
        # Track
        await flags.track_usage(feature_name, current_user, is_enabled)
    
    return enabled_features

# Frontend usage
@router.post("/api/v1/messages/send")
async def send_message(
    request: SendMessageRequest,
    current_user: str = Depends(get_current_user),
    flags: FeatureFlags = Depends(get_feature_flags)
):
    """Send message with feature flag checks"""
    
    # Check if E2E encryption is enabled
    e2e_enabled = await flags.is_enabled('end_to_end_encryption', current_user)
    
    if e2e_enabled and request.is_encrypted:
        # Process encrypted message
        message = await encrypt_and_store_message(request)
    else:
        # Plain text message
        message = await store_message(request)
    
    return message
