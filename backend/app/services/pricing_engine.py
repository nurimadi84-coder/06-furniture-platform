"""Deterministic furniture pricing engine."""

from __future__ import annotations

from app.schemas.calculator import (
    CalculatorInputSchema,
    CalculatorResultSchema,
    CostBreakdownSchema,
    ExtraOption,
    FurnitureType,
    HardwareBrand,
    MaterialGrade,
)

# Material factor = KZT per m³ of envelope volume (W×H×D after mm→m)
MATERIAL_FACTORS: dict[MaterialGrade, float] = {
    MaterialGrade.ECONOMY: 85_000.0,
    MaterialGrade.STANDARD: 120_000.0,
    MaterialGrade.PREMIUM: 180_000.0,
}

TYPE_MULTIPLIERS: dict[FurnitureType, float] = {
    FurnitureType.WARDROBE: 1.0,
    FurnitureType.KITCHEN: 1.35,
    FurnitureType.BED: 0.85,
}

HARDWARE_COSTS: dict[HardwareBrand, float] = {
    HardwareBrand.BASIC: 25_000.0,
    HardwareBrand.BLUM: 75_000.0,
    HardwareBrand.DTC: 55_000.0,
}

ASSEMBLY_COSTS: dict[FurnitureType, float] = {
    FurnitureType.WARDROBE: 40_000.0,
    FurnitureType.KITCHEN: 90_000.0,
    FurnitureType.BED: 30_000.0,
}

EXTRA_COSTS: dict[ExtraOption, float] = {
    ExtraOption.LIGHTING: 18_000.0,
    ExtraOption.DRAWERS: 35_000.0,
    ExtraOption.MIRRORS: 22_000.0,
}


class PricingEngine:
    """Calculate Cost = (W×H×D×MaterialFactor) + Hardware + Assembly (+ extras)."""

    @staticmethod
    def calculate(payload: CalculatorInputSchema) -> CalculatorResultSchema:
        dims = payload.dimensions
        # Cost = (W × H × D × MaterialFactor) with dimensions in metres
        volume_m3 = (dims.width / 1000) * (dims.height / 1000) * (dims.depth / 1000)

        material_factor = MATERIAL_FACTORS[payload.material_grade]
        type_mult = TYPE_MULTIPLIERS[payload.furniture_type]

        material_cost = round(volume_m3 * material_factor * type_mult, 2)
        hardware_cost = HARDWARE_COSTS[payload.hardware_brand]
        assembly_cost = ASSEMBLY_COSTS[payload.furniture_type]
        extras_cost = round(
            sum(EXTRA_COSTS[opt] for opt in payload.extra_options),
            2,
        )

        base_cost = round(
            material_cost + hardware_cost + assembly_cost + extras_cost,
            2,
        )
        price_min = round(base_cost * 0.95, 2)
        price_max = round(base_cost * 1.15, 2)

        options_text = (
            ", ".join(opt.value for opt in payload.extra_options)
            if payload.extra_options
            else "без доп. опций"
        )
        summary = (
            f"{payload.furniture_type.value.capitalize()}: "
            f"{dims.width}×{dims.height}×{dims.depth} мм, "
            f"материал «{payload.material_grade.value}», "
            f"фурнитура «{payload.hardware_brand.value}», {options_text}."
        )

        return CalculatorResultSchema(
            furniture_type=payload.furniture_type,
            price_min=price_min,
            price_max=price_max,
            breakdown=CostBreakdownSchema(
                material_cost=material_cost,
                hardware_cost=hardware_cost,
                assembly_cost=assembly_cost,
                extras_cost=extras_cost,
                base_cost=base_cost,
            ),
            summary=summary,
        )
