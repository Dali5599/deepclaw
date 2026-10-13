"""
DeepClaw WebSocket Module
Gestion des connexions WebSocket pour la diffusion de recherche en direct
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ResearchConnection:
    """Gère une connexion WebSocket pour un utilisateur"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.session_id = None
        self.topic = None
        self.is_active = True
    
    async def send(self, data: dict):
        """Envoyer un message via WebSocket"""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"Erreur d'envoi WebSocket : {e}")
            self.is_active = False
    
    async def send_text(self, text: str):
        """Envoyer un message texte"""
        try:
            await self.websocket.send_text(text)
        except Exception as e:
            logger.error(f"Erreur d'envoi texte WebSocket : {e}")
            self.is_active = False


class WebSocketManager:
    """Gestionnaire de toutes les connexions WebSocket actives"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, ResearchConnection] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str = None, topic: str = None):
        """Nouvelle connexion WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id:
            connection = ResearchConnection(websocket)
            connection.session_id = session_id
            connection.topic = topic
            self.session_connections[session_id] = connection
            await connection.send({
                "type": "connected",
                "session_id": session_id,
                "topic": topic,
                "message": f"Connected to research session: {session_id}"
            })
        logger.info(f"WebSocket connecté (actifs: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket, session_id: str = None):
        """Déconnexion"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id and session_id in self.session_connections:
            del self.session_connections[session_id]
        logger.info(f"WebSocket déconnecté (actifs: {len(self.active_connections)})")
    
    async def broadcast(self, message: dict):
        """Diffuser un message à tous les clients connectés"""
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Erreur d'envoi broadcast: {e}")
                if ws in self.active_connections:
                    self.active_connections.remove(ws)
    
    async def broadcast_to_session(self, session_id: str, data: dict):
        """Diffuser un message à une session spécifique"""
        if session_id in self.session_connections:
            await self.session_connections[session_id].send(data)
    
    def get_active_sessions(self) -> Set[str]:
        """Retourner les IDs des sessions actives"""
        return set(self.session_connections.keys())
    
    def get_connection(self, session_id: str) -> Optional[ResearchConnection]:
        """Obtenir une connexion spécifique"""
        return self.session_connections.get(session_id)


# Instance singleton
manager = WebSocketManager()
ws_manager = manager
