# /backend/app/services/analytics_service.py
"""
Track business metrics and user analytics
"""

class AnalyticsService:
    
    async def track_event(
        self,
        user_id: str,
        event_type: str,
        properties: dict = None,
        timestamp: datetime = None
    ):
        """Track user event"""
        
        event = {
            'user_id': user_id,
            'event_type': event_type,
            'properties': properties or {},
            'timestamp': timestamp or datetime.utcnow().isoformat()
        }
        
        # Send to analytics queue
        await cache.xadd('analytics:events', event)
        
        # Publish to specific stream
        await cache.publish(f'analytics:{event_type}', json.dumps(event))
    
    async def get_user_metrics(self, user_id: str, days: int = 30) -> dict:
        """Get metrics for user"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'groups_joined': 0,
            'active_days': 0,
            'last_active': None
        }
        
        # Messages sent
        result = await db.execute(
            select(func.count(Message.id)).where(
                Message.sender_id == user_id,
                Message.created_at >= cutoff_date
            )
        )
        metrics['messages_sent'] = result.scalar() or 0
        
        # Groups joined
        result = await db.execute(
            select(func.count(GroupMember.id)).where(
                GroupMember.user_id == user_id,
                GroupMember.joined_at >= cutoff_date
            )
        )
        metrics['groups_joined'] = result.scalar() or 0
        
        # Last active
        result = await db.execute(
            select(Message.created_at).where(
                Message.sender_id == user_id
            ).order_by(Message.created_at.desc()).limit(1)
        )
        row = result.scalar()
        if row:
            metrics['last_active'] = row.isoformat()
        
        return metrics
