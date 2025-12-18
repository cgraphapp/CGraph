"""
Feature flags for gradual rollout and A/B testing
"""

import json
from enum import Enum

class FeatureFlags(str, Enum):
    # New features
    VOICE_MESSAGES = "voice_messages"
    VIDEO_CALLS = "video_calls"
    COSMETICS_SHOP_V2 = "cosmetics_shop_v2"
    DARK_MODE = "dark_mode"
    
    # Experimental
    AI_MODERATION = "ai_moderation"
    FEDERATED_SEARCH = "federated_search"
    
    # Deprecating
    OLD_MESSAGE_FORMAT = "old_message_format"

class FeatureFlagManager:
    
    def __init__(self, db_session):
        self.db = db_session
        self.cache = {}
    
    async def is_enabled(self, feature: FeatureFlags, user_id: str = None) -> bool:
        """
        Check if feature is enabled for user
        Supports rollout percentages and user whitelisting
        """
        
        # Check cache first
        cache_key = f"feature:{feature}:{user_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get feature config
        config = await self.get_feature_config(feature)
        
        if not config or not config['enabled']:
            return False
        
        # Check rollout percentage
        if config['rollout_percentage'] < 100:
            # Use consistent hashing to determine if user is in rollout
            if user_id:
                hash_value = int(hashlib.md5(
                    f"{user_id}:{feature}".encode()
                ).hexdigest(), 16) % 100
                if hash_value >= config['rollout_percentage']:
                    return False
        
        # Check whitelist/blacklist
        if user_id:
            if user_id in config.get('whitelist', []):
                return True
            if user_id in config.get('blacklist', []):
                return False
        
        result = True
        self.cache[cache_key] = result
        return result
    
    async def get_feature_config(self, feature: FeatureFlags) -> dict:
        """Get feature flag configuration"""
        
        # Fetch from database or cache
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.name == feature)
        )
        flag = result.scalar()
        
        if not flag:
            return None
        
        return {
            'enabled': flag.enabled,
            'rollout_percentage': flag.rollout_percentage,
            'whitelist': flag.whitelist or [],
            'blacklist': flag.blacklist or [],
            'config': flag.config or {}
        }

# Usage in API endpoints
async def send_message(content: str, user_id: str, db_session):
    """Send message"""
    
    # Check if voice messages are enabled
    if await feature_flags.is_enabled(FeatureFlags.VOICE_MESSAGES, user_id):
        # Enable voice message support
        message_type = "voice" if content.startswith("voice://") else "text"
    else:
        message_type = "text"
    
    # Continue with message creation...