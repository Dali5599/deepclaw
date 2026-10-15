"""
DeepClaw Web Collectors Package
Modules pour la collecte de sources depuis divers moteurs de recherche
"""
from .web_collector import WebCollector, SearchResult
from .html_parser import HTMLParser

# Compatibilité alias
BraveSearchCollector = WebCollector
DuckDuckGoCollector = WebCollector

__all__ = [
    "WebCollector",
    "SearchResult",
    "BraveSearchCollector",
    "DuckDuckGoCollector",
    "HTMLParser"
]
