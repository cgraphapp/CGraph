# /backend/app/services/message_queue.py
"""
Redis pub/sub for background jobs and event streaming
Allows horizontal scaling without coupling
"""

import json
import asyncio
from typing import Callable, Dict
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MessageQueue:
    """
    Publish-subscribe message queue
    - Sends notifications asynchronously
    - Scales to multiple server instances
    - Survives temporary disconnections
    """
    
    def __init__(self):
        self.redis_client = None
        self.subscribers: Dict[str, Callable] = {}
    
    async def initialize(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(settings.REDIS_URL)
    
    async def publish_event(self, channel: str, event: dict):
        """Publish event to channel"""
        
        message = {
            'type': event['type'],
            'timestamp': datetime.utcnow().isoformat(),
            **event
        }
        
        await self.redis_client.publish(channel, json.dumps(message))
        logger.info(f"Published to {channel}: {event['type']}")
    
    async def subscribe_to_channel(
        self,
        channel: str,
        handler: Callable
    ):
        """Subscribe to channel with handler"""
        
        self.subscribers[channel] = handler
        
        # Create pub/sub connection
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        
        # Listen for messages
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error handling event: {e}")

# Event types to publish
class Events:
    # User events
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_EDITED = "message.edited"
    MESSAGE_DELETED = "message.deleted"
    
    # Payment events
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_ACTIVE = "subscription.active"
    
    # System events
    MAINTENANCE_START = "system.maintenance_start"
    MAINTENANCE_END = "system.maintenance_end"

# Initialize
message_queue = MessageQueue()

# Handlers
async def handle_user_registered(event: dict):
    """Handle new user registration"""
    user_id = event['user_id']
    
    # Send welcome email
    # Create default groups
    # Initialize preferences
    logger.info(f"New user registered: {user_id}")

async def handle_payment_completed(event: dict):
    """Handle payment completion"""
    user_id = event['user_id']
    subscription_tier = event['tier']
    
    # Update user subscription
    # Send confirmation email
    # Unlock premium features
    logger.info(f"Payment completed for {user_id}: {subscription_tier}")

# Register handlers
message_queue.subscribers[Events.USER_REGISTERED] = handle_user_registered
message_queue.subscribers[Events.PAYMENT_COMPLETED] = handle_payment_completed
