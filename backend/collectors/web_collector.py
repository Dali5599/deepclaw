"""
DeepClaw Web Collector - Brave Search + DuckDuckGo + HTML Parser
"""
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from ..core import settings
from ..db.models import Source, Fact, Contradiction

logger = logging.getLogger(__name__)


class SearchResult:
    """Résultat d'une recherche"""
    def __init__(self, source_id: str, url: str, title: str, content: str, 
                 relevance: float, source_type: str, fetched_at: float):
        self.source_id = source_id
        self.url = url
        self.title = title
        self.content = content
        self.relevance = relevance
        self.source_type = source_type
        self.fetched_at = fetched_at


class WebCollector:
    """Collecteur de sources web unifié"""
    
    def __init__(self, settings: dict):
        self.settings = settings
        self.session = None
        
    async def initialize(self):
        """Initialiser la session HTTP"""
        import aiohttp
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Lancer une recherche et récupérer les sources"""
        if not self.session:
            await self.initialize()
        
        # Utiliser Brave Search en priorité
        results = await self._brave_search(query, max_results)
        
        # Fallback sur DuckDuckGo si Brave échoue
        if not results:
            results = await self._duckduckgo_search(query, max_results)
        
        # Nettoyer et convertir en Source objects
        sources = []
        for item in results:
            source = self._parse_source(item)
            if source:
                sources.append(source)
        
        return sources
    
    async def _brave_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Recherche via Brave Search API"""
        import aiohttp
        
        url = "https://api.brave.search/v1/search"
        params = {
            "q": query,
            "count": max_results,
            "language": "en",
            "safe": "high"
        }
        
        try:
            async with self.session.post(url, params=params) as response:
                data = await response.json()
                if isinstance(data, dict) and "results" in data:
                    for result in data["results"][:max_results]:
                        source = self._parse_brave_result(result)
                        if source:
                            yield source
        except Exception as e:
            logger.error(f"Brave search error: {e}")
    
    async def _duckduckgo_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Recherche via DuckDuckGo (fallback)"""
        import aiohttp
        
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "nonindexed": "false",
            "skip_disambig": "true"
        }
        
        try:
            async with self.session.post(url, params=params) as response:
                data = await response.json()
                if "Abstract" in data:
                    for result in data["Abstract"][:max_results]:
                        source = self._parse_duckduckgo_result(result)
                        if source:
                            yield source
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
    
    def _parse_brave_result(self, result: dict) -> Optional[SearchResult]:
        """Parser un résultat Brave Search"""
        # Brave Search API structure
        title = result.get("title", "") or result.get("title", "Unknown")
        url = result.get("url", "")
        content = result.get("content", "") or ""
        relevance = result.get("score", 0.0)
        source_type = result.get("source", "unknown")
        
        return SearchResult(
            source_id=f"brave_{result.get('id', 'unknown')}",
            url=url,
            title=title,
            content=content,
            relevance=relevance,
            source_type=source_type,
            fetched_at=time.time()
        )
    
    def _parse_duckduckgo_result(self, result: dict) -> Optional[SearchResult]:
        """Parser un résultat DuckDuckGo"""
        title = result.get("title", "") or result.get("title", "Unknown")
        url = result.get("url", "")
        content = result.get("text", "") or ""
        relevance = result.get("score", 0.0)
        source_type = result.get("source", "duckduckgo")
        
        return SearchResult(
            source_id=f"ddg_{result.get('id', 'unknown')}",
            url=url,
            title=title,
            content=content,
            relevance=relevance,
            source_type=source_type,
            fetched_at=time.time()
        )
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
