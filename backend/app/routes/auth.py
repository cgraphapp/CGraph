from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db
from app.models import User
from app.services.auth import AuthService
from app.cache import cache

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

@router.post("/auth/register", status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register new user with email and password"""
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=request.email,
        username=request.username,
        password_hash=AuthService.hash_password(request.password),
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "message": "User registered successfully"
    }

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    
    # Get user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not AuthService.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    access_token = AuthService.create_access_token(user.id)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )

@router.get("/auth/me")
async def get_current_user(
    token: str = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = AuthService.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
    }
