"""
API routes.
"""
from fastapi import APIRouter

from app.api.v1 import api_router as api_v1_router

# Create API router
api_router = APIRouter()

# Include API v1 router
api_router.include_router(api_v1_router)
