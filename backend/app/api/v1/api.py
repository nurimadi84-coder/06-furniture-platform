"""Aggregate API v1 routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import calculator, leads, tracking, vision

api_router = APIRouter()
api_router.include_router(calculator.router)
api_router.include_router(leads.router)
api_router.include_router(vision.router)
api_router.include_router(tracking.router)
