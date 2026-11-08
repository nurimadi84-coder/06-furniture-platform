"""Lead (callback / quote request) ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LeadStatus(str, enum.Enum):
    """Lifecycle status of a sales lead."""

    NEW = "new"
    CONTACTED = "contacted"
    MEASURING = "measuring"
    CLOSED = "closed"


def _lead_status_values(enum_cls: type[LeadStatus]) -> list[str]:
    return [member.value for member in enum_cls]


class Lead(Base):
    """Client request captured from the calculator form."""

    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    client_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    furniture_type: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_price_min: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_price_max: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            values_callable=_lead_status_values,
            native_enum=False,
            validate_strings=True,
        ),
        default=LeadStatus.NEW,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
