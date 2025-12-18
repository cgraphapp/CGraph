# /backend/app/security/session_management.py
"""
Session tracking and concurrent login limits
"""

class SessionManager:
    
    MAX_CONCURRENT_SESSIONS = 5  # Per user
    SESSION_TIMEOUT = 3600 * 24  # 24 hours
    
    async def create_session(
        self,
        user_id: str,
        device_info: dict,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create new session"""
        
        # Check concurrent sessions
        sessions = await self._get_active_sessions(user_id)
        
        if len(sessions) >= self.MAX_CONCURRENT_SESSIONS:
            # Remove oldest session
            oldest = min(sessions, key=lambda s: s['created_at'])
            await self._remove_session(oldest['session_id'])
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'device_info': device_info,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        # Store in Redis
        await cache.setex(
            f"session:{session_id}",
            self.SESSION_TIMEOUT,
            json.dumps(session)
        )
        
        logger.info(f"Session created for user {user_id}")
        
        return session_id
    
    async def _get_active_sessions(self, user_id: str) -> list:
        """Get all active sessions for user"""
        
        # Scan all session keys
        cursor = 0
        sessions = []
        
        while True:
            cursor, keys = await cache.scan(cursor, match="session:*")
            
            for key in keys:
                session_data = await cache.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session['user_id'] == user_id:
                        sessions.append(session)
            
            if cursor == 0:
                break
        
        return sessions
    
    async def _remove_session(self, session_id: str):
        """Revoke session"""
        
        await cache.delete(f"session:{session_id}")
