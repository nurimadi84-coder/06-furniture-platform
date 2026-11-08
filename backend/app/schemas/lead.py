"""Pydantic schemas for leads and order tracking."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.schemas.calculator import FurnitureType


KZ_PHONE_PATTERN = re.compile(r"^(\+77|87)\d{9}$")


class LeadStatusSchema(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    MEASURING = "measuring"
    CLOSED = "closed"


class LeadCreateSchema(BaseModel):
    """Payload for creating a new sales lead."""

    client_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., description="Kazakhstan phone: +77XXXXXXXXX or 87XXXXXXXXX")
    furniture_type: FurnitureType
    estimated_price_min: float = Field(..., ge=0)
    estimated_price_max: float = Field(..., ge=0)

    @field_validator("phone")
    @classmethod
    def validate_kz_phone(cls, value: str) -> str:
        cleaned = value.strip().replace(" ", "").replace("-", "")
        if not KZ_PHONE_PATTERN.match(cleaned):
            raise ValueError(
                "Некорректный номер. Формат: +77XXXXXXXXX или 87XXXXXXXXX"
            )
        if cleaned.startswith("87"):
            return "+7" + cleaned[1:]
        return cleaned

    @field_validator("estimated_price_max")
    @classmethod
    def max_gte_min(cls, value: float, info: ValidationInfo) -> float:
        min_price = info.data.get("estimated_price_min")
        if min_price is not None and value < min_price:
            raise ValueError("estimated_price_max must be >= estimated_price_min")
        return value


class LeadResponseSchema(BaseModel):
    """Lead record returned to the client."""

    id: str
    client_name: str
    phone: str
    furniture_type: str
    estimated_price_min: float
    estimated_price_max: float
    status: LeadStatusSchema
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderStageSchema(str, Enum):
    MEASURING = "measuring"
    CUTTING = "cutting"
    ASSEMBLY = "assembly"
    DELIVERY = "delivery"
    COMPLETED = "completed"


class TrackingStageSchema(BaseModel):
    """Single step in the workshop progress bar."""

    key: OrderStageSchema
    label: str
    completed: bool
    current: bool


class TrackingResponseSchema(BaseModel):
    """Public order tracking payload."""

    order_number: str
    client_name: str
    current_stage: OrderStageSchema
    stage_photo_url: str | None
    stages: list[TrackingStageSchema]
    updated_at: datetime


class VisionEstimateResponseSchema(BaseModel):
    """Values extracted from a sketch for calculator autofill."""

    furniture_type: FurnitureType | None = None
    width: int | None = None
    height: int | None = None
    depth: int | None = None
    material_grade: str | None = None
    notes: str = ""
    source: str = "heuristic"
