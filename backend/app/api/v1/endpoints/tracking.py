"""Public order tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.order import Order, OrderStage
from app.schemas.lead import (
    OrderStageSchema,
    TrackingResponseSchema,
    TrackingStageSchema,
)

router = APIRouter(prefix="/tracking", tags=["tracking"])

STAGE_ORDER: list[tuple[OrderStage, str]] = [
    (OrderStage.MEASURING, "Замер"),
    (OrderStage.CUTTING, "Раскрой"),
    (OrderStage.ASSEMBLY, "Сборка"),
    (OrderStage.DELIVERY, "Монтаж"),
    (OrderStage.COMPLETED, "Готово"),
]


def build_stages(current: OrderStage) -> list[TrackingStageSchema]:
    current_idx = next(
        (i for i, (stage, _) in enumerate(STAGE_ORDER) if stage == current),
        0,
    )
    stages: list[TrackingStageSchema] = []
    for idx, (stage, label) in enumerate(STAGE_ORDER):
        stages.append(
            TrackingStageSchema(
                key=OrderStageSchema(stage.value),
                label=label,
                completed=idx < current_idx or current == OrderStage.COMPLETED,
                current=idx == current_idx and current != OrderStage.COMPLETED,
            )
        )
    if current == OrderStage.COMPLETED:
        for stage in stages:
            stage.completed = True
            stage.current = stage.key == OrderStageSchema.COMPLETED
    return stages


@router.get("/{order_number}", response_model=TrackingResponseSchema)
async def get_order_status(
    order_number: str,
    db: AsyncSession = Depends(get_db),
) -> TrackingResponseSchema:
    """Return current workshop stage and photo for a public order code."""
    result = await db.execute(
        select(Order).where(Order.order_number == order_number.strip().upper())
    )
    order = result.scalar_one_or_none()

    # Also try exact match for mixed-case codes like TEST1234
    if order is None:
        result = await db.execute(
            select(Order).where(Order.order_number == order_number.strip())
        )
        order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден.")

    return TrackingResponseSchema(
        order_number=order.order_number,
        client_name=order.client_name,
        current_stage=OrderStageSchema(order.current_stage.value),
        stage_photo_url=order.stage_photo_url,
        stages=build_stages(order.current_stage),
        updated_at=order.updated_at,
    )
