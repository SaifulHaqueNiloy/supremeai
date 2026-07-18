from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from core.config import settings


DATABASE_URL = settings.supabase_database_url

if not DATABASE_URL:
    logger.warning("SUPABASE_DATABASE_URL_POOLER is missing. Database operations will fail.")


# বাংলা মন্তব্য: কানেকশন স্ট্রিংয়ে postgresql:// বা postgres:// থাকলে তা asyncpg-এর জন্য postgresql+asyncpg:// দিয়ে প্রতিস্থাপন করা হচ্ছে
def get_async_url(url: str) -> str:
    if not url:
        return "sqlite+aiosqlite:///:memory:"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


_async_url = get_async_url(DATABASE_URL)

# বাংলা মন্তব্য: MyPy টাইপ ইনফারেন্সের সমস্যা সমাধানের জন্য টাইপ হিসেবে dict[str, Any] ব্যবহার করা হলো
engine_kwargs: dict[str, Any] = {
    "echo": False,
}
if _async_url.startswith("sqlite"):
    engine_kwargs["poolclass"] = StaticPool
    engine_kwargs["connect_args"] = {"check_same_thread": False}
if _async_url.startswith("postgresql"):
    engine_kwargs.update(
        {
            "pool_size": 20,
            "max_overflow": 0,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            # বাংলা মন্তব্য: PgBouncer এর transaction pool মোডের সাথে সামঞ্জস্যের জন্য statement_cache_size=0 করা হলো
            "connect_args": {
                "command_timeout": 30,
                "server_settings": {"application_name": "supremeai_2.0"},
                "statement_cache_size": 0,
            },
        }
    )

engine = create_async_engine(_async_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for backend tasks or non-FastAPI usages.

    বাংলা: FastAPI-এর বাইরে বা ব্যাকগ্রাউন্ড টাস্কে ডাটাবেস সেশন ব্যবহারের জন্য।
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
            raise
        finally:
            await session.close()


# FastAPI Dependency Injection (with safe rollback)
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for database sessions.

    বাংলা: FastAPI রুটগুলোর জন্য ডাটাবেস ডিপেন্ডেন্সি।
    """
    async with get_db_session_context() as session:
        yield session
