"""Routes package"""
from fastapi import APIRouter
from .research import router as research_router
from .reports import router as reports_router

router = APIRouter()
router.include_router(research_router)
router.include_router(reports_router)

__all__ = ["router", "research_router", "reports_router"]
