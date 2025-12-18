from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import secrets
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.models import User, Session

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hash.encode())

    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if not expires_delta:
            expires_delta = timedelta(hours=JWT_EXPIRE_HOURS)
        
        expire = datetime.utcnow() + expires_delta
        to_encode = {"sub": user_id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: str, device_name: str, ip_address: str, user_agent: str
    ) -> str:
        """Create new session"""
        token = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        
        session = Session(
            user_id=user_id,
            token=token,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        return token

    @staticmethod
    async def verify_session(db: AsyncSession, token: str) -> Optional[str]:
        """Verify session token and return user_id"""
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        
        if not session or session.expires_at < datetime.utcnow():
            return None
        
        # Update last activity
        session.last_activity_at = datetime.utcnow()
        await db.commit()
        return session.user_id

    @staticmethod
    async def revoke_session(db: AsyncSession, token: str) -> bool:
        """Revoke session token"""
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False

print("✅ Auth service configured")
