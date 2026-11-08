"""Pydantic schemas for the pricing calculator."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class FurnitureType(str, Enum):
    WARDROBE = "шкаф"
    KITCHEN = "кухня"
    BED = "кровать"


class MaterialGrade(str, Enum):
    ECONOMY = "эконом"
    STANDARD = "стандарт"
    PREMIUM = "премиум"


class HardwareBrand(str, Enum):
    BASIC = "базовая"
    BLUM = "Blum"
    DTC = "DTC"


class ExtraOption(str, Enum):
    LIGHTING = "подсветка"
    DRAWERS = "выдвижные ящики"
    MIRRORS = "зеркала"


class DimensionsSchema(BaseModel):
    """Furniture dimensions in millimetres."""

    width: int = Field(..., ge=300, le=6000, description="Width in mm")
    height: int = Field(..., ge=300, le=3500, description="Height in mm")
    # Upper bound 2500 covers bed length mapped as depth/length in the quiz
    depth: int = Field(..., ge=200, le=2500, description="Depth/length in mm")


class CalculatorInputSchema(BaseModel):
    """Input payload for instant price estimation."""

    furniture_type: FurnitureType
    dimensions: DimensionsSchema
    material_grade: MaterialGrade = MaterialGrade.STANDARD
    hardware_brand: HardwareBrand = HardwareBrand.BASIC
    extra_options: list[ExtraOption] = Field(default_factory=list)

    @field_validator("extra_options")
    @classmethod
    def unique_options(cls, value: list[ExtraOption]) -> list[ExtraOption]:
        return list(dict.fromkeys(value))


class CostBreakdownSchema(BaseModel):
    """Detailed cost components in KZT."""

    material_cost: float
    hardware_cost: float
    assembly_cost: float
    extras_cost: float
    base_cost: float


class CalculatorResultSchema(BaseModel):
    """Price range returned by the pricing engine."""

    furniture_type: FurnitureType
    currency: Literal["KZT"] = "KZT"
    price_min: float
    price_max: float
    breakdown: CostBreakdownSchema
    summary: str
