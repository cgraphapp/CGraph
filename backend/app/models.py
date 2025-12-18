from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL for wallet-only users
    
    # Wallet authentication
    wallet_id = Column(String(255), unique=True, nullable=True, index=True)
    wallet_public_key = Column(Text, nullable=True)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    mfa_backup_codes = Column(Text, nullable=True)  # JSON array
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        {"schema": None},
    )

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False)
    device_id = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        {"schema": None},
    )

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(255), nullable=False, index=True)
    sender_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_encrypted = Column(Text, nullable=True)  # Encrypted version
    
    message_type = Column(String(50), default="text")  # text, image, file, etc.
    status = Column(String(50), default="delivered")  # pending, delivered, failed
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        {"schema": None},
    )

print("✅ Models defined")
