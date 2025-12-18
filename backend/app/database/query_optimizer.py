# /backend/app/database/query_optimizer.py
"""
Database query optimization techniques
"""

class QueryOptimizer:
    
    @staticmethod
    async def get_messages_with_optimization(room_id: str, limit: int = 50):
        """
        Optimized query with:
        - Eager loading of relationships
        - Pagination
        - Indexed columns
        - Query caching
        """
        
        # Check cache first
        cache_key = f"messages:room_{room_id}:limit_{limit}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached
        
        # Query with relationships loaded
        result = await db.execute(
            select(Message)
            .where(Message.room_id == room_id)
            .options(
                joinedload(Message.sender),  # Eager load sender
                joinedload(Message.reactions)  # Eager load reactions
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        messages = result.unique().scalars().all()
        
        # Cache result
        await cache_manager.set(cache_key, messages, ttl=300)
        
        return messages
    
    @staticmethod
    def use_database_indexes():
        """
        Critical indexes for common queries
        """
        
        # Example migrations:
        """
        -- Messages by room
        CREATE INDEX idx_messages_room_created ON messages(room_id, created_at DESC);
        
        -- Users by email (login)
        CREATE INDEX idx_users_email ON users(email);
        
        -- Group members
        CREATE INDEX idx_group_members_user_group ON group_members(user_id, group_id);
        
        -- Message search
        CREATE INDEX idx_messages_content_gin ON messages USING GIN(content);
        """
