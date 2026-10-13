"""
Reports Routes - API for accessing and downloading research reports
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


class ReportItem(BaseModel):
    id: str
    topic: str
    created_at: str
    report_url: str
    pdf_url: Optional[str] = None
    markdown_url: Optional[str] = None


@router.get("/", response_model=List[ReportItem])
async def get_all_reports():
    """Liste de tous les rapports générés."""
    return []


@router.get("/{report_id}")
async def get_report_detail(report_id: str):
    """Détail d'un rapport de recherche."""
    return {
        "id": report_id,
        "status": "ready",
        "format": "pdf",
        "url": f"/api/reports/{report_id}/download"
    }
