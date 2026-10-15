"""
DeepClaw Fact Extractor - Extraction de faits à partir de sources web
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from ..db.models import Fact, Source, Session
from ..collectors.web_collector import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class FactExtractor:
    """Extrait des faits structurés à partir de sources web"""
    
    def __init__(self, session: "Session"):
        self.session = session
    
    async def extract_from_source(self, source: Source) -> List[Fact]:
        """
        Extraire les faits à partir d'une source web
        
        Args:
            source: Objet Source représentant la source extraite
            
        Returns:
            Liste de faits extraits
        """
        # Utiliser le parseur HTML pour extraire le texte
        text = self._clean_html_text(source.content)
        
        # Détecter les entités et relations
        facts = []
        
        # Extraction basique de phrases clés
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            # Chercher des entités (noms propres, dates, nombres)
            entities = self._extract_entities(sentence)
            
            # Si la phrase contient des informations factuelles
            if self._is_fact_sentence(sentence):
                fact = self._create_fact_from_sentence(sentence, entities)
                if fact:
                    facts.append(fact)
        
        return facts
    
    def _clean_html_text(self, html: str) -> str:
        """Nettoyer le texte HTML en texte pur"""
        try:
            from .html_parser import clean_html_content
            return clean_html_content(html)
        except ImportError:
            # Fallback simple
            return re.sub(r'<[^>]+>', ' ', html)
    
    def _extract_entities(self, sentence: str) -> List[Dict]:
        """Extraire les entités (personnes, organisations, lieux, dates, etc.)"""
        # Regex simples pour extraire des entités
        entities = []
        
        # Personnes (ex: "John Smith", "Alice Johnson")
        person_pattern = r'(?i)(?:\b(John|Mary|Sarah|David|Robert|Emily|Michael|Jennifer)\b)'
        persons = re.findall(person_pattern, sentence)
        if persons:
            entities.extend([{'type': 'person', 'value': p} for p in persons])
        
        # Organisations (ex: "Google", "Microsoft", "Apple")
        org_pattern = r'(?i)(?:\b(Google|Microsoft|Apple|Amazon|Facebook|Meta|Twitter|LinkedIn)\b)'
        orgs = re.findall(org_pattern, sentence)
        if orgs:
            entities.extend([{'type': 'organization', 'value': o} for o in orgs])
        
        # Lieux (ex: "Paris", "New York", "London")
        loc_pattern = r'(?i)(?:\b(Paris|New+York|London|Tokyo|Berlin|Madrid|Sydney)\b)'
        locations = re.findall(loc_pattern, sentence)
        if locations:
            entities.extend([{'type': 'location', 'value': l} for l in locations])
        
        # Dates
        date_patterns = [
            r'(?i)(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'(?i)(\b(January|February|March|April|May|June|July|August|September|October|November|December)\b)',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, sentence)
            if matches:
                entities.extend([{'type': 'date', 'value': m} for m in matches])
        
        return entities
    
    def _is_fact_sentence(self, sentence: str) -> bool:
        """Déterminer si une phrase est une déclaration factuelle"""
        # Une phrase est considérée comme factuelle si elle contient des entités
        # et des verbes d'action (être, faire, avoir, etc.)
        fact_verbs = ['be', 'have', 'is', 'are', 'was', 'were', 'does', 'did', 
                      'found', 'created', 'developed', 'published', 'released']
        
        words = sentence.lower().split()
        has_fact_verb = any(word in fact_verbs for word in words)
        has_entity = len(self._extract_entities(sentence)) > 0
        
        return has_fact_verb and has_entity
    
    def _create_fact_from_sentence(self, sentence: str, entities: List[Dict]) -> Optional[Fact]:
        """Créer un objet Fact à partir d'une phrase et de ses entités"""
        # Simplified fact creation
        # In a real implementation, this would use NLP libraries
        # for better entity linking and relation extraction
        
        # Try to construct a meaningful fact
        fact_text = f"{sentence}"
        
        # Add source reference
        fact_text += f" | Source: {source.url}"
        
        # Create basic fact structure
        return Fact(
            id=f"fact_{len(facts)}",
            session_id=source.session_id,
            content=fact_text,
            entity_ids=[e['value'] for e in entities],
            extracted_at=time.time(),
            confidence=0.75  # Placeholder
        )


# Fact types
@dataclass
class Fact:
    """Représentation d'un fait extrait"""
    id: str
    session_id: str
    content: str
    entity_ids: List[str]
    extracted_at: float
    confidence: float = 0.0
    
    def __repr__(self):
        return f"Fact(id={self.id}, content='{self.content[:50]}...', confidence={self.confidence})"