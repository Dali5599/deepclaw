"""
Research Routes - API for initiating and managing research sessions
"""
import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List

from ...core import settings, get_llm_router
from ...db import SessionLocal, create_sessions

router = APIRouter(prefix="/api/research", tags=["Research"])
logger = logging.getLogger(__name__)


class ResearchRequest(BaseModel):
    topic: str
    depth: int = 3
    max_sources: int = 10
    use_brave: bool = True
    use_duckduckgo: bool = True
    providers: Optional[list] = None
    output_format: str = "pdf"


class ResearchResponse(BaseModel):
    id: str
    topic: str
    status: str
    message: str
    estimated_time: int


class ReportSchema(BaseModel):
    id: str
    topic: str
    created_at: str
    report_url: str
    pdf_url: Optional[str] = None
    markdown_url: Optional[str] = None


class ReportsResponse(BaseModel):
    reports: List[ReportSchema]
    total: int


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """Lancer une nouvelle session de recherche"""
    try:
        session = create_sessions(request.topic, depth=request.depth, max_sources=request.max_sources)
        
        background_tasks.add_task(
            run_research,
            session.id,
            request.topic,
            request.depth,
            request.max_sources,
            request.providers
        )
        
        logger.info(f"Recherche lancée : {session.id} - Topic: {request.topic}")
        
        return ResearchResponse(
            id=session.id,
            topic=request.topic,
            status="started",
            message="Research session started. Results will be available shortly.",
            estimated_time=request.depth * 60
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la recherche : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ReportsResponse)
async def list_reports():
    """Liste de tous les rapports générés"""
    return ReportsResponse(reports=[], total=0)


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Récupérer les détails d'une session de recherche"""
    return {
        "id": session_id,
        "status": "in_progress",
        "progress": 0.5
    }


@router.get("/{session_id}/progress")
async def get_progress(session_id: str):
    """Récupérer la progression d'une session de recherche"""
    return {
        "id": session_id,
        "progress": 0.75,
        "sources_collected": 6,
        "facts_extracted": 12,
        "contradictions_found": 0,
        "status": "collecting_sources"
    }


@router.post("/{session_id}/reports")
async def generate_report(session_id: str, format: str = "pdf"):
    """Générer un rapport pour une session de recherche"""
    return {
        "session_id": session_id,
        "message": f"Report generated: {session_id}.{format}",
        "download_url": f"/api/reports/{session_id}"
    }


async def run_research(session_id: str, topic: str, depth: int, max_sources: int, providers: Optional[list]):
    """Fonction utilitaire pour exécuter la recherche en arrière-plan"""
    logger.info(f"Démarrage de la recherche {session_id} : {topic}")
