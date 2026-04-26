from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# SQLite needs connect_args={"check_same_thread": False} for FastAPI concurrency
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False}
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
