"""
config/database.py
──────────────────
Async SQLAlchemy engine + session factory.
FastAPI dependency `get_db` yields a session per request.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings


# ── Async engine ────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # logs SQL queries in debug mode
    pool_pre_ping=True,           # verify connections before use
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ─────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # keep objects usable after commit
    autoflush=False,
    autocommit=False,
)


# ── Base class for all ORM models ────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    Yields an async DB session for the lifetime of a single request.
    Usage in router:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (called on app startup)."""
    async with engine.begin() as conn:
        # Import all models so Base knows about them
        from app.models import user, gig, order, review, message  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
