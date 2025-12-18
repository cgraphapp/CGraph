# /backend/app/services/push_notification_service.py
"""
Push notifications for iOS and Android
"""

import firebase_admin
from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)

class PushNotificationService:
    
    def __init__(self):
        # Initialize Firebase
        firebase_admin.initialize_app()
        self.messaging = messaging
    
    async def send_to_user(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict = None,
        priority: str = "high"
    ) -> bool:
        """
        Send push notification to user's devices
        """
        
        # Get user's device tokens
        devices = await self._get_user_devices(user_id)
        
        if not devices:
            logger.info(f"No devices found for user {user_id}")
            return False
        
        tokens = [d.fcm_token for d in devices if d.fcm_token]
        
        if not tokens:
            return False
        
        try:
            # Build message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        click_action="FLUTTER_NOTIFICATION_CLICK"
                    )
                ),
                apns=messaging.APNSConfig(
                    headers={
                        "apns-priority": "10" if priority == "high" else "5"
                    }
                ),
                tokens=tokens
            )
            
            # Send
            response = messaging.send_multicast(message)
            
            # Log results
            logger.info(
                f"Push sent to {response.success_count}/{len(tokens)} devices "
                f"for user {user_id}"
            )
            
            # Handle failures
            for i, error in enumerate(response.errors):
                if error:
                    logger.error(f"Failed to send to {tokens[i]}: {str(error)}")
                    
                    # Mark token as invalid if necessary
                    if error.code == "invalid-argument":
                        await self._mark_token_invalid(tokens[i])
            
            return response.success_count > 0
        
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return False
    
    async def _get_user_devices(self, user_id: str):
        """Get all devices for user"""
        
        result = await db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.is_active == True
            )
        )
        
        return result.scalars().all()
    
    async def _mark_token_invalid(self, token: str):
        """Mark FCM token as invalid"""
        
        device = await db.execute(
            select(UserDevice).where(UserDevice.fcm_token == token)
        )
        device = device.scalar()
        
        if device:
            device.is_active = False
            await db.commit()
