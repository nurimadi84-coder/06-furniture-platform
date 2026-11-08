"""Async SQLAlchemy engine and session helpers."""

from collections.abc import AsyncGenerator
import logging

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI dependencies."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def _normalize_enum_columns(conn) -> None:  # type: ignore[no-untyped-def]
    """Rewrite legacy Enum *names* (ASSEMBLY) to *values* (assembly)."""
    from app.models.lead import LeadStatus
    from app.models.order import OrderStage

    for stage in OrderStage:
        await conn.execute(
            text(
                "UPDATE orders SET current_stage = :value "
                "WHERE current_stage = :name OR current_stage = :value_upper"
            ),
            {
                "value": stage.value,
                "name": stage.name,
                "value_upper": stage.value.upper(),
            },
        )

    for status in LeadStatus:
        await conn.execute(
            text(
                "UPDATE leads SET status = :value "
                "WHERE status = :name OR status = :value_upper"
            ),
            {
                "value": status.value,
                "name": status.name,
                "value_upper": status.value.upper(),
            },
        )


async def init_db() -> None:
    """Create tables, normalize enum storage, seed demo tracking order."""
    from app.models import Lead, Order  # noqa: F401
    from app.models.order import OrderStage

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite may already hold enum member names from earlier builds
        try:
            await _normalize_enum_columns(conn)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Enum normalization skipped: %s", exc)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.order_number == "TEST1234")
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(
                Order(
                    order_number="TEST1234",
                    client_name="Демо Клиент",
                    current_stage=OrderStage.ASSEMBLY,
                    stage_photo_url=(
                        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800"
                    ),
                )
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                logger.info("Demo order TEST1234 already exists (race)")
        elif existing.current_stage != OrderStage.ASSEMBLY:
            # Keep demo predictable for acceptance checks
            existing.current_stage = OrderStage.ASSEMBLY
            if not existing.stage_photo_url:
                existing.stage_photo_url = (
                    "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800"
                )
            await session.commit()
