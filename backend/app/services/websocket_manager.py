# /backend/app/services/websocket_manager.py
"""
WebSocket connection management for real-time messaging
Uses pub/sub for horizontal scalability
"""

import json
import asyncio
from typing import Dict, Set, Callable
from fastapi import WebSocket
import redis.asyncio as redis
from app.config import settings

class ConnectionManager:
    """Manages active WebSocket connections"""
    
    def __init__(self):
        # Room ID -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # User ID -> Set of WebSocket connections (for direct messages)
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
        # Redis for pub/sub across multiple instances
        self.redis = None
    
    async def init_redis(self):
        """Initialize Redis pub/sub"""
        self.redis = await redis.from_url(settings.REDIS_URL)
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Register new WebSocket connection"""
        await websocket.accept()
        
        # Add to room connections
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Subscribe to room events
        await self.redis.subscribe(f"room:{room_id}")
        
        # Subscribe to user-specific events
        await self.redis.subscribe(f"user:{user_id}")
    
    async def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        """Unregister WebSocket connection"""
        
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
    
    async def broadcast_to_room(self, room_id: str, message: dict):
        """Broadcast message to all users in room"""
        
        # Publish via Redis (reaches all server instances)
        await self.redis.publish(f"room:{room_id}", json.dumps(message))
        
        # Also send to local connections for low latency
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        
        await self.redis.publish(f"user:{user_id}", json.dumps(message))
        
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user: {e}")

# Create global instance
ws_manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time messaging"""
    
    # Verify token
    user_id = verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Verify user is member of room
    db = SessionLocal()
    member = await db.execute(
        select(RoomMember).where(
            (RoomMember.room_id == room_id) &
            (RoomMember.user_id == user_id)
        )
    )
    if not member.scalar():
        await websocket.close(code=4003, reason="Not a member")
        return
    
    # Connect
    await ws_manager.connect(websocket, room_id, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data['type'] == 'message':
                # Save to database
                message = Message(
                    room_id=room_id,
                    sender_id=user_id,
                    content=data['content'],
                    is_encrypted=data.get('is_encrypted', False)
                )
                db.add(message)
                await db.commit()
                
                # Broadcast to room
                await ws_manager.broadcast_to_room(room_id, {
                    'type': 'message',
                    'message_id': str(message.id),
                    'sender_id': user_id,
                    'content': data['content'],
                    'timestamp': message.created_at.isoformat()
                })
            
            elif data['type'] == 'typing':
                # Broadcast typing indicator
                await ws_manager.broadcast_to_room(room_id, {
                    'type': 'typing',
                    'user_id': user_id,
                    'is_typing': data['is_typing']
                })
            
            elif data['type'] == 'reaction':
                # Add emoji reaction
                # ... implementation
                pass
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, room_id, user_id)
        await db.close()
