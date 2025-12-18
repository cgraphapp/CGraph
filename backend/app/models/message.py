"""Message model"""

from sqlalchemy import Column, String, DateTime, UUID as SQLUUID, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(255), nullable=False, index=True)
    sender_id = Column(SQLUUID(as_uuid=True), nullable=False, index=True)
    content = Column(String(4096), nullable=False)
    
    # Media
    media_urls = Column(JSON, default=list)
    
    # Encryption
    is_encrypted = Column(Boolean, default=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Reactions
    reactions = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message(id={self.id}, room_id={self.room_id})>"
