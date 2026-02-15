from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"),
    connect_args={"check_same_thread": False}
)

# Async engine for API
async_engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    """Initialize database tables"""
    from app.models.database import Task, Image

    # Create tables
    from sqlalchemy import inspect
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()

    if not tables:
        Base.metadata.create_all(bind=sync_engine)
        print("Database tables created successfully")
