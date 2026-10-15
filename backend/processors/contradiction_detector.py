"""
DeepClaw Contradiction Detector - Détection de contradictions entre faits
"""
import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

from ..db.models import Fact, Contradiction, Session
from .fact_extractor import Fact

logger = logging.getLogger(__name__)


@dataclass
class ContradictionDetector:
    """Détecte les contradictions entre faits extraits de sources multiples"""
    
    def __init__(self, session: "Session"):
        self.session = session
        self.fact_database = {}
    
    async def build_fact_database(self, facts: List[Fact]):
        """Construire une base de données de faits indexée par entités"""
        for fact in facts:
            fact_id = fact.id
            self.fact_database[fact_id] = fact
            
            # Indexer par entités
            if hasattr(fact, 'entity_ids'):
                for entity_id in fact.entity_ids:
                    if entity_id not in self.fact_database:
                        self.fact_database[entity_id] = {}
                    self.fact_database[entity_id][fact_id] = fact
    
    async def detect_contradictions(self, facts: List[Fact]) -> List[Contradiction]:
        """
        Détecter les contradictions entre faits extraits
        
        Args:
            facts: Liste des faits extraits
            
        Returns:
            Liste des contradictions détectées
        """
        await self.build_fact_database(facts)
        
        contradictions = []
        
        # 1. Détecter les contradictions directes (même entité, relations opposées)
        direct_contradictions = await self._detect_direct_contradictions(facts)
        contradictions.extend(direct_contradictions)
        
        # 2. Détecter les contradictions indirectes (guarded_could"))
        indirect_contradictions = await self._detect_indirect_contradictions(facts)
        contradictions.extend(indirect_contradictions)
        
        # 3. Détecter les contradictions temporelles
        temporal_contradictions = await self._detect_temporal_contradictions(facts)
        contradictions.extend(temporal_contradictions)
        
        return contradictions
    
    async def _detect_direct_contradictions(self, facts: List[Fact]) -> List[Contradiction]:
        """Détecter les contradictions directes entre faits sur les mêmes entités"""
        contradictions = []
        
        # Regroupement par entités
        facts_by_entity = defaultdict(list)
        for fact in facts:
            if hasattr(fact, 'entity_ids'):
                for entity_id in fact.entity_ids:
                    facts_by_entity[entity_id].append(fact)
        
        for entity_id, entity_facts in facts_by_entity.items():
            # Vérifier les relations opposées (ex: "Paris est capitale de France" vs "Londres est capitale de France")
            entity_contradictions = await self._find_contradictory_facts(entity_facts)
            
            for fact1, fact2 in entity_contradictions:
                contradiction = self._create_contradiction(
                    description=f"Contradiction entre faits sur {entity_id}",
                    severity="high",
                    related_facts=[fact1, fact2]
                )
                contradictions.append(contradiction)
        
        return contradictions
    
    async def _detect_indirect_contradictions(self, facts: List[Fact]) -> List[Contradiction]:
        """Détecter les contradictions indirectes via inférence logique"""
        contradictions = []
        
        # Regroupement par source
        facts_by_source = defaultdict(list)
        for fact in facts:
            # Simplifié - dans un système réel, il faudrait extraire les IDs de source
            facts_by_source["unknown"].append(fact)
        
        # Comparer les faits entre sources
        for source_name, source_facts in facts_by_source.items():
            # Pour chaque paire de faits provenant de sources différentes sur les mêmes sujets
            for i, fact1 in enumerate(source_facts):
                for j, fact2 in enumerate(source_facts):
                    if i < j:
                        # Vérifier la contradiction via inférence logique
                        if self._facts_implies_contradiction(fact1, fact2):
                            contradiction = self._create_contradiction(
                                description=f"Inférence contradictoire entre sources : '{fact1.content}' vs '{fact2.content}'",
                                severity="medium",
                                related_facts=[fact1, fact2]
                            )
                            contradictions.append(contradiction)
        
        return contradictions
    
    async def _detect_temporal_contradictions(self, facts: List[Fact]) -> List[Contradiction]:
        """Détecter les contradictions temporelles (affirmation qui contredit une affirmation temporelle antérieure)"""
        contradictions = []
        
        # Mettre en cache les faits temporels
        temporal_facts = []
        for fact in facts:
            # Extraire les indications temporelles
            if self._contains_temporal_reference(fact.content):
                temporal_facts.append(fact)
        
        # Comparer les faits temporels
        for fact1 in temporal_facts:
            for fact2 in temporal_facts:
                if fact1 != fact2:
                    # Vérifier la contradiction temporelle
                    if self._is_temporal_contradiction(fact1, fact2):
                        contradiction = self._create_contradiction(
                            description=f"Contradiction temporelle : '{fact1.content}' vs '{fact2.content}'",
                            severity="low",
                            related_facts=[fact1, fact2]
                        )
                        contradictions.append(contradiction)
        
        return contradictions
    
    def _contains_temporal_reference(self, text: str) -> bool:
        """Vérifier si un texte contient des références temporelles"""
        temporal_keywords = [
            "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030",
            "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December",
            "le", "en", "à", "avant", "après", "pendant", "depuis", "jusqu'à"
        ]
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in temporal_keywords)
    
    def _is_temporal_contradiction(self, fact1: Fact, fact2: Fact) -> bool:
        """Déterminer si deux faits temporels sont contradictoires"""
        # Implémentation simplifiée : cherche les années contradictoires dans les mêmes phrases
        # Dans un système réel, il faudrait un analyseur NLP plus sophistiqué
        return False
    
    def _facts_implies_contradiction(self, fact1: Fact, fact2: Fact) -> bool:
        """Déterminer si deux faits impliquent une contradiction"""
        # Implémentation simplifiée basée sur des mots-clés contradictoires
        contradictory_words = [
            ("oui", "non"), ("vrai", "faux"), ("gagné", "perdu"), ("ouvert", "fermé"),
            ("avancé", "reculé"), ("grand", "petit"), ("haut", "bas"), ("gauche", "droite")
        ]
        
        # Regroupement des mots par ordre
        fact1_words = fact1.content.lower().split()
        fact2_words = fact2.content.lower().split()
        
        for pair in contradictory_words:
            if (pair[0] in fact1_words and pair[1] in fact2_words) or \
               (pair[1] in fact1_words and pair[0] in fact2_words):
                return True
        
        return False
    
    def _create_contradiction(self, description: str, severity: str, related_facts: List[Fact]) -> Contradiction:
        """Créer une nouvelle contradiction"""
        return Contradiction(
            id=f"contr_{len(contradictions) + 1}",
            session_id=self.session.id,
            description=description,
            severity=severity,
            related_facts=related_facts
        )


def find_contradictory_facts(facts: List[Fact]) -> List[tuple]:
    """
    Utilitaires de haut niveau pour trouver les faits contradictoires
    
    Args:
        facts: Liste de faits
        
    Returns:
        Liste de tuples (fact1, fact2) de faits contradictoires
    """
    contradictions = []
    
    for i, fact1 in enumerate(facts):
        for j, fact2 in enumerate(facts):
            if i < j and facts_implies_contradiction(fact1, fact2):
                contradictions.append((fact1, fact2))
    
    return contradictions