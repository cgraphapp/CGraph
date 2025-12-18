# /backend/app/models/pricing.py
"""
Pricing models and tier definitions
"""

from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class PricingTable:
    """
    Pricing configuration
    Updated: December 2025
    """
    
    TIERS = {
        "free": {
            "name": "Free",
            "price_monthly": 0,
            "price_annual": 0,
            "stripe_price_id": None,
            "features": {
                "max_users_per_group": 10,
                "max_messages_stored": 10000,
                "message_history_days": 30,
                "file_uploads_per_month": 100,
                "max_file_size_mb": 10,
                "end_to_end_encryption": False,
                "sso": False,
                "api_access": False,
                "support_level": "community"
            }
        },
        
        "premium": {
            "name": "Premium",
            "price_monthly": 9.99,
            "price_annual": 99.99,
            "stripe_price_id": "price_premium_monthly",
            "stripe_price_id_annual": "price_premium_annual",
            "features": {
                "max_users_per_group": 500,
                "max_messages_stored": 1000000,
                "message_history_days": 365,
                "file_uploads_per_month": 10000,
                "max_file_size_mb": 100,
                "end_to_end_encryption": True,
                "sso": False,
                "api_access": True,
                "support_level": "email"
            }
        },
        
        "enterprise": {
            "name": "Enterprise",
            "price_monthly": "custom",
            "price_annual": "custom",
            "stripe_price_id": None,
            "features": {
                "max_users_per_group": -1,  # Unlimited
                "max_messages_stored": -1,
                "message_history_days": -1,
                "file_uploads_per_month": -1,
                "max_file_size_mb": -1,
                "end_to_end_encryption": True,
                "sso": True,
                "api_access": True,
                "support_level": "24/7",
                "custom_branding": True,
                "multi_tenancy": True,
                "compliance": True
            }
        }
    }
    
    @staticmethod
    def get_tier(tier_name: str):
        return PricingTable.TIERS.get(tier_name)
    
    @staticmethod
    def get_feature_limit(tier_name: str, feature: str):
        tier = PricingTable.TIERS.get(tier_name, {})
        return tier.get("features", {}).get(feature)
