# /backend/app/database/transactions.py
"""
Database transaction management for ACID compliance
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class TransactionManager:
    
    @staticmethod
    @asynccontextmanager
    async def transaction(db: AsyncSession, isolation_level="READ_COMMITTED"):
        """
        Managed transaction context
        Handles rollback on error, ensures ACID compliance
        """
        try:
            # Set isolation level
            await db.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
            
            await db.begin()
            logger.debug(f"Transaction started (isolation: {isolation_level})")
            
            yield db
            
            await db.commit()
            logger.debug("Transaction committed")
        
        except Exception as e:
            await db.rollback()
            logger.error(f"Transaction rolled back: {str(e)}")
            raise

# Usage
async def transfer_credits(db: AsyncSession, from_user_id: str, to_user_id: str, amount: int):
    """Transfer credits between users (ACID transaction)"""
    
    async with TransactionManager.transaction(db, isolation_level="SERIALIZABLE"):
        # Get users with lock
        from_user = await db.execute(
            select(User).where(User.id == from_user_id).with_for_update()
        )
        from_user = from_user.scalar()
        
        if not from_user or from_user.credits < amount:
            raise InsufficientCreditsError()
        
        to_user = await db.execute(
            select(User).where(User.id == to_user_id).with_for_update()
        )
        to_user = to_user.scalar()
        
        if not to_user:
            raise UserNotFoundError()
        
        # Deduct and add
        from_user.credits -= amount
        to_user.credits += amount
        
        # Log transaction
        transaction_log = TransactionLog(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=amount,
            timestamp=datetime.utcnow()
        )
        db.add(transaction_log)
        
        await db.commit()
        logger.info(f"Transferred {amount} credits from {from_user_id} to {to_user_id}")
