"""Message endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/dm/send")
async def send_dm(
    recipient_id: str,
    content: str,
    db: AsyncSession = Depends(get_db)
):
    """Send direct message"""
    # TODO: Implement DM sending
    return {"message": "DM endpoint ready"}

@router.get("/dm/{conversation_id}")
async def get_dm_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get DM conversation history"""
    # TODO: Implement history retrieval
    return {"messages": []}
