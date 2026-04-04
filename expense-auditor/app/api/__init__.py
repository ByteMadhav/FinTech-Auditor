"""
API routes.
"""
from fastapi import APIRouter

from app.api.router import api_router as endpoints_router

# Create API router
api_router = APIRouter()

# Include endpoints router
api_router.include_router(endpoints_router)
