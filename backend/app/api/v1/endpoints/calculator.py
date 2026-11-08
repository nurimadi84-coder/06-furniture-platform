"""Calculator API endpoints."""

from fastapi import APIRouter

from app.schemas.calculator import CalculatorInputSchema, CalculatorResultSchema
from app.services.pricing_engine import PricingEngine

router = APIRouter(prefix="/calculator", tags=["calculator"])


@router.post("/calculate", response_model=CalculatorResultSchema)
async def calculate_price(payload: CalculatorInputSchema) -> CalculatorResultSchema:
    """Return an instant price range for the given configuration."""
    return PricingEngine.calculate(payload)
