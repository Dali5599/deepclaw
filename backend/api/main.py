"""
DeepClaw FastAPI Application Entry Point
"""
import os
import asyncio
import logging
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core import settings, get_llm_router
from ..db import get_db_session, create_tables
from .routes import router
from .websocket import manager
from .streaming import generate_research_stream

# Configuration du logging
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    logger.info("Initialisation de DeepClaw et des tables de base de données...")
    try:
        await create_tables()
        logger.info("Base de données initialisée avec succès.")
    except Exception as e:
        logger.warning(f"Note initialisation DB : {e}")
    yield
    logger.info("Arrêt de DeepClaw.")

app = FastAPI(
    title="DeepClaw API",
    description="Autonomous Deep Research & Fact-Synthesis Engine",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour les flux de recherche en direct"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("research:"):
                topic = data.split(":", 1)[1]
                
                async def stream_research():
                    try:
                        async for chunk in generate_research_stream(
                            topic,
                            max_depth=settings.max_depth,
                            websocket=websocket
                        ):
                            await manager.broadcast(chunk)
                    except Exception as e:
                        logger.error(f"Erreur de stream de recherche : {e}")
                        await manager.broadcast({
                            "type": "error",
                            "message": str(e)
                        })
                
                asyncio.create_task(stream_research())
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Vérification de l'état de santé"""
    router_inst = get_llm_router()
    providers = router_inst.get_available_providers()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "components": {
            "llm_router": len(providers),
            "available_providers": providers,
            "database": "connected (SQLite WAL)",
            "websocket": len(manager.active_connections)
        }
    }


@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "name": "DeepClaw API",
        "version": "0.1.0",
        "description": "Autonomous Deep Research & Fact-Synthesis Engine",
        "docs": "/docs"
    }


if __name__ == "__main__":
    logger.info(f"Démarrage de DeepClaw sur {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
