"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/email/register")
async def register_email(
    email: str,
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Register user with email"""
    # TODO: Implement registration
    return {"message": "Registration endpoint ready"}

@router.post("/email/login")
async def login_email(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Login with email"""
    # TODO: Implement login
    return {"message": "Login endpoint ready"}
