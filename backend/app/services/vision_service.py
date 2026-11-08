"""Sketch / photo analysis for calculator autofill."""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.calculator import FurnitureType
from app.schemas.lead import VisionEstimateResponseSchema

logger = logging.getLogger(__name__)

# Keep in sync with DimensionsSchema bounds
DIM_BOUNDS = {
    "width": (300, 6000),
    "height": (300, 3500),
    "depth": (200, 2500),
}

SYSTEM_PROMPT = """
You are a furniture design assistant. Analyze the sketch/photo and extract:
- furniture_type: one of "шкаф", "кухня", "кровать" (or null)
- width, height, depth in millimetres (integers, or null if unknown)
  Constraints: width 300-6000, height 300-3500, depth 200-2500
- material_grade: "эконом", "стандарт", or "премиум" if inferable
- notes: short Russian comment

Return ONLY valid JSON with keys:
furniture_type, width, height, depth, material_grade, notes
""".strip()


def clamp_dimension(kind: str, value: int | None) -> int | None:
    """Clamp a dimension into calculator-accepted bounds."""
    if value is None:
        return None
    low, high = DIM_BOUNDS[kind]
    return max(low, min(high, value))


class VisionService:
    """Use OpenAI Vision when configured; otherwise heuristic fallback."""

    def __init__(self) -> None:
        self._api_key = get_settings().OPENAI_API_KEY.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def estimate_sketch(
        self,
        file_bytes: bytes,
        content_type: str,
        filename: str,
    ) -> VisionEstimateResponseSchema:
        if self.is_configured:
            try:
                return await self._call_openai(file_bytes, content_type)
            except Exception as exc:  # noqa: BLE001
                logger.error("OpenAI vision failed, using fallback: %s", exc)

        return self._heuristic_estimate(filename)

    async def _call_openai(
        self,
        file_bytes: bytes,
        content_type: str,
    ) -> VisionEstimateResponseSchema:
        mime = content_type or "image/jpeg"
        b64 = base64.b64encode(file_bytes).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"

        payload: dict[str, Any] = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Извлеки параметры мебели для калькулятора.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                },
            ],
            "max_tokens": 400,
            "temperature": 0.1,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        parsed = self._parse_json_content(content)
        return self._to_schema(parsed, source="openai")

    def _heuristic_estimate(self, filename: str) -> VisionEstimateResponseSchema:
        """Fallback when OpenAI is unavailable — bounds-safe defaults."""
        lower = filename.lower()
        furniture_type: FurnitureType = FurnitureType.WARDROBE
        if any(token in lower for token in ("kitchen", "кухн", "kuh")):
            furniture_type = FurnitureType.KITCHEN
        elif any(token in lower for token in ("bed", "кров", "krov")):
            furniture_type = FurnitureType.BED

        # (width, height, depth) — all within DimensionsSchema
        defaults = {
            FurnitureType.WARDROBE: (1800, 2400, 600),
            FurnitureType.KITCHEN: (3000, 2100, 600),
            FurnitureType.BED: (1600, 900, 2000),
        }
        width, height, depth = defaults[furniture_type]

        return VisionEstimateResponseSchema(
            furniture_type=furniture_type,
            width=width,
            height=height,
            depth=depth,
            material_grade="стандарт",
            notes=(
                "OPENAI_API_KEY не задан или Vision недоступен. "
                "Подставлены типовые размеры — проверьте вручную."
            ),
            source="heuristic",
        )

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        content = content.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if fence:
            content = fence.group(1).strip()
        return json.loads(content)

    @staticmethod
    def _to_schema(
        parsed: dict[str, Any],
        source: str,
    ) -> VisionEstimateResponseSchema:
        furniture_raw = parsed.get("furniture_type")
        furniture_type: FurnitureType | None = None
        if furniture_raw:
            try:
                furniture_type = FurnitureType(str(furniture_raw).lower())
            except ValueError:
                furniture_type = None

        def as_int(value: Any) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return VisionEstimateResponseSchema(
            furniture_type=furniture_type,
            width=clamp_dimension("width", as_int(parsed.get("width"))),
            height=clamp_dimension("height", as_int(parsed.get("height"))),
            depth=clamp_dimension("depth", as_int(parsed.get("depth"))),
            material_grade=parsed.get("material_grade"),
            notes=str(parsed.get("notes") or ""),
            source=source,
        )
