from typing import AsyncGenerator
import motor.motor_asyncio
import aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bookstore.infrastructure.persistance.repository.sql.models import metadata

POSTGRES_URL = "postgresql+asyncpg://postgres:amin1998@localhost:5432/BookStore(ddd)"
MONGODB_URL = "mongodb://localhost:27017"
REDIS_URL = "redis://localhost:6379"


postgres_engine = create_async_engine(POSTGRES_URL, echo=True,  pool_size=5,max_overflow=10)

async_session = sessionmaker(postgres_engine,class_=AsyncSession,expire_on_commit=False)

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
mongo_db = mongo_client.bookstore

redis_client = aioredis.from_url(REDIS_URL,encoding="utf-8",decode_responses=True)


async def init_db() -> None:
    async with postgres_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db_connections() -> None:
    await postgres_engine.dispose()
    mongo_client.close()
    await redis_client.close()