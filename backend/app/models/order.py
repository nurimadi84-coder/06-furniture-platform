"""Order tracking ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrderStage(str, enum.Enum):
    """Production stages visible to the client."""

    MEASURING = "measuring"
    CUTTING = "cutting"
    ASSEMBLY = "assembly"
    DELIVERY = "delivery"
    COMPLETED = "completed"


def _order_stage_values(enum_cls: type[OrderStage]) -> list[str]:
    return [member.value for member in enum_cls]


class Order(Base):
    """Furniture order with workshop progress."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    client_name: Mapped[str] = mapped_column(String(120), nullable=False)
    current_stage: Mapped[OrderStage] = mapped_column(
        Enum(
            OrderStage,
            values_callable=_order_stage_values,
            native_enum=False,
            validate_strings=True,
        ),
        default=OrderStage.MEASURING,
        nullable=False,
    )
    stage_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
