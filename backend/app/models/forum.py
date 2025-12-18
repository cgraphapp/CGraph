# /backend/app/models/forum.py
"""
Complete forum system with posts, threads, moderation, roles
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

class Forum(Base):
    __tablename__ = "forums"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    slug = Column(String(100), unique=True)
    category = Column(String(50))  # general, tech, community, etc.
    
    # Settings
    is_public = Column(Boolean, default=True)
    allow_anonymous = Column(Boolean, default=False)
    require_approval = Column(Boolean, default=False)
    
    # Permissions
    permissions = Column(JSONB, default={})
    
    # Moderation
    moderator_ids = Column(JSONB, default=[])
    banned_users = Column(JSONB, default=[])
    
    # Stats
    total_posts = Column(Integer, default=0)
    total_members = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class ForumThread(Base):
    __tablename__ = "forum_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forum_id = Column(UUID(as_uuid=True), ForeignKey("forums.id"))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    title = Column(String(500), nullable=False)
    slug = Column(String(255), unique=True)
    content = Column(Text)
    
    # Pinned/Locked
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    pin_position = Column(Integer)
    
    # Status
    status = Column(String(20), default="active")  # active, archived, deleted
    
    # Tags
    tags = Column(JSONB, default=[])
    
    # Stats
    reply_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Moderation
    approved = Column(Boolean, default=True)
    flagged_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class ForumPost(Base):
    __tablename__ = "forum_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("forum_threads.id"))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    content = Column(Text, nullable=False)
    
    # Position in thread
    position = Column(Integer)  # First post = 1
    is_original_post = Column(Boolean)
    
    # Status
    status = Column(String(20), default="active")
    approved = Column(Boolean, default=True)
    
    # Engagement
    likes = Column(Integer, default=0)
    liked_by = Column(JSONB, default=[])  # User IDs
    
    # Moderation
    flagged_count = Column(Integer, default=0)
    edited_by_mod = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class ForumModeration(Base):
    __tablename__ = "forum_moderation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forum_id = Column(UUID(as_uuid=True), ForeignKey("forums.id"))
    
    # What's being moderated
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("forum_threads.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Moderation action
    action = Column(String(50))  # approve, reject, delete, warn, ban
    reason = Column(Text)
    
    # Who did it
    moderator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # If temporary
    duration_days = Column(Integer)
    expires_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
