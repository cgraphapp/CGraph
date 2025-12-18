from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event
import os

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL_REPLICA = os.getenv("DATABASE_URL_REPLICA")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"timeout": 30, "server_settings": {"application_name": "cgraph"}},
)

# Read replica engine
replica_engine = create_async_engine(
    DATABASE_URL_REPLICA,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"timeout": 30},
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, future=True
)

# Replica session
AsyncSessionReplica = sessionmaker(
    replica_engine, class_=AsyncSession, expire_on_commit=False, future=True
)

# Base class for models
Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db_replica() -> AsyncSession:
    """Dependency for read-only queries"""
    async with AsyncSessionReplica() as session:
        try:
            yield session
        finally:
            await session.close()
