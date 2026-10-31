import urllib.parse as up
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings


def configure_database(raw_url: str):
    db_url = raw_url
    engine_args = {"echo": False}

    if "sqlite" in db_url:
        engine_args["connect_args"] = {"check_same_thread": False}
    elif "postgres" in db_url or "postgresql" in db_url:
        # Standardize dialect for asyncpg
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Parse query params and sanitize for asyncpg
        # asyncpg requires ?ssl=require and fails on ?sslmode=require or ?channel_binding
        parsed = up.urlparse(db_url)
        query_params = up.parse_qs(parsed.query) if parsed.query else {}
        needs_ssl = "sslmode" in query_params or "ssl" in query_params or "neon.tech" in parsed.netloc

        new_query = "ssl=require" if needs_ssl else ""
        db_url = up.urlunparse(parsed._replace(query=new_query))

        # PgBouncer connection pooling options
        engine_args["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
        engine_args["pool_pre_ping"] = True
        engine_args["pool_recycle"] = 300

    return db_url, engine_args


database_url, engine_args = configure_database(settings.DATABASE_URL)
engine = create_async_engine(database_url, **engine_args)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initializes tables in database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
