"""Lead capture API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreateSchema, LeadResponseSchema
from app.services.telegram_notifier import TelegramNotifierService

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/create", response_model=LeadResponseSchema, status_code=201)
async def create_lead(
    payload: LeadCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Lead:
    """Validate phone, persist lead, and notify Telegram asynchronously."""
    lead = Lead(
        client_name=payload.client_name.strip(),
        phone=payload.phone,
        furniture_type=payload.furniture_type.value,
        estimated_price_min=payload.estimated_price_min,
        estimated_price_max=payload.estimated_price_max,
        status=LeadStatus.NEW,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    notifier = TelegramNotifierService()
    background_tasks.add_task(notifier.notify_new_lead, payload)

    return lead
