"""Async Telegram Bot API notifications."""

from __future__ import annotations

import html
import logging

import httpx

from app.core.config import get_settings
from app.schemas.lead import LeadCreateSchema

logger = logging.getLogger(__name__)


class TelegramNotifierService:
    """Send formatted lead alerts to a Telegram chat."""

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.TELEGRAM_BOT_TOKEN.strip()
        self._chat_id = settings.TELEGRAM_CHAT_ID.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._chat_id)

    def format_lead_message(self, lead: LeadCreateSchema) -> str:
        name = html.escape(lead.client_name)
        phone = html.escape(lead.phone)
        furniture = html.escape(lead.furniture_type.value)
        return (
            "<b>Новая заявка MebelExpress</b>\n"
            f"Клиент: <b>{name}</b>\n"
            f"Телефон: <code>{phone}</code>\n"
            f"Мебель: {furniture}\n"
            f"Оценка: {lead.estimated_price_min:,.0f} – "
            f"{lead.estimated_price_max:,.0f} ₸"
        )

    async def notify_new_lead(self, lead: LeadCreateSchema) -> bool:
        """Post a lead notification. Returns False if skipped or failed."""
        if not self.is_configured:
            logger.warning(
                "Telegram credentials missing — lead notification skipped"
            )
            return False

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": self.format_lead_message(lead),
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("Telegram notification failed: %s", exc)
            return False
