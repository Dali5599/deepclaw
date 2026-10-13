"""
DeepClaw Database Session Management
Async SQLite with WAL mode support
"""
import logging
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from ..config import settings
from .models import Base, Session as SessionModel, ResearchStatus

logger = logging.getLogger(__name__)

database_url = settings.database_url
if database_url.startswith("sqlite://"):
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    database_url,
    echo=getattr(settings, "database_echo", False),
    future=True
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in str(database_url):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Compatibility query wrapper for legacy routes if needed
class _CompatQuery:
    def __init__(self, model):
        self.model = model
    def get(self, ident):
        return None
    def filter_by(self, **kwargs):
        class _Result:
            def all(self):
                return []
        return _Result()

class SessionLocalWrapper:
    """Wrapper providing both async sessionmaker and query compatibility."""
    def __call__(self, *args, **kwargs):
        return async_session_factory(*args, **kwargs)
    @property
    def query(self):
        return _CompatQuery(SessionModel)

SessionLocal = SessionLocalWrapper()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

get_db_session = get_async_session

def create_sessions(topic: str, depth: int = 3, max_sources: int = 10, **kwargs):
    """Instantiate a new research Session object."""
    return SessionModel(
        id=str(uuid.uuid4()),
        topic=topic,
        depth=depth,
        max_sources=max_sources,
        status=ResearchStatus.PENDING,
        **kwargs
    )

async def create_tables():
    """Create all database tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")

async def drop_tables():
    """Drop all database tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully.")
