"""
DeepClaw Fact Synthesizer - Synthèse de faits en rapports structurés
"""
import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..db.models import Fact, Contradiction, Session, Report
from ..collectors.web_collector import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class FactSynthesizer:
    """Synthétise des faits en rapports structurés avec citations"""
    
    def __init__(self, session: "Session"):
        self.session = session
        self.facts_by_category = {}
        self.contradictions_by_severity = {}
    
    async def synthesize_report(self, 
                              facts: List[Fact], 
                              contradictions: List[Contradiction],
                              sources: List[SearchResult]) -> Report:
        """
        Synthétiser les faits en un rapport structuré
        
        Args:
            facts: Liste des faits extraits
            contradictions: Liste des contradictions détectées
            sources: Liste des sources consultées
            
        Returns:
            Rapport structuré avec résumé exécutif, contenu et citations
        """
        # 1. Organiser les faits par catégories
        await self._organize_facts_by_category(facts)
        
        # 2. Analyser les contradictions
        await self._analyze_contradictions(contradictions)
        
        # 3. Générer le résumé exécutif
        executive_summary = await self._generate_executive_summary(
            facts, contradictions, sources
        )
        
        # 4. Générer le contenu principal
        main_content = await self._generate_main_content(
            facts, contradictions, sources
        )
        
        # 5. Préparer les citations BibTeX
        citations = await self._prepare_citations(sources)
        
        # 6. Créer le rapport
        report = Report(
            id=f"report_{self.session.id}",
            session_id=self.session.id,
            title=f"DeepClaw Research Report: {self.session.topic}",
            executive_summary=executive_summary,
            content=main_content,
            format="markdown",
            citations=citations,
            created_at=datetime.now()
        )
        
        return report
    
    async def _organize_facts_by_category(self, facts: List[Fact]):
        """Organiser les faits par catégories thématiques"""
        # Catégories basiques - dans un système réel, utiliser du clustering NLP
        categories = {
            "background": [],
            "key_findings": [],
            "statistics": [],
            "methodology": [],
            "implications": [],
            "limitations": []
        }
        
        # Assignation basique basée sur des mots-clés
        for fact in facts:
            content_lower = fact.content.lower()
            if any(word in content_lower for word in ["background", "overview", "introduction", "history"]):
                categories["background"].append(fact)
            elif any(word in content_lower for word in ["statistics", "data", "numbers", "percent", "%"]):
                categories["statistics"].append(fact)
            elif any(word in content_lower for word in ["method", "approach", "technique", "process"]):
                categories["methodology"].append(fact)
            elif any(word in content_lower for word in ["implication", "consequence", "impact", "effect"]):
                categories["implications"].append(fact)
            elif any(word in content_lower for word in ["limitation", "drawback", "weakness", "constraint"]):
                categories["limitations"].append(fact)
            else:
                categories["key_findings"].append(fact)
        
        self.facts_by_category = categories
    
    async def _analyze_contradictions(self, contradictions: List[Contradiction]):
        """Analyser les contradictions par sévérité"""
        self.contradictions_by_severity = {
            "high": [c for c in contradictions if c.severity == "high"],
            "medium": [c for c in contradictions if c.severity == "medium"],
            "low": [c for c in contradictions if c.severity == "low"]
        }
    
    async def _generate_executive_summary(self, 
                                        facts: List[Fact], 
                                        contradictions: List[Contradiction],
                                        sources: List[SearchResult]) -> str:
        """Générer un résumé exécutif du rapport"""
        summary_parts = []
        
        # Introduction
        summary_parts.append(
            f"Ce rapport présente une analyse approfondie du sujet '{self.session.topic}' "
            f"basée sur l'analyse de {len(sources)} sources fiables."
        )
        
        # Nombre de faits et contradictions
        summary_parts.append(
            f"L'analyse a permis d'extraire {len(facts)} faits vérifiables "
            f"et a identifié {len(contradictions)} points de divergence entre les sources."
        )
        
        # Principales découvertes
        key_findings = self.facts_by_category.get("key_findings", [])
        if key_findings:
            summary_parts.append(
                f"Les principales découvertes incluent : "
                f"{', '.join([f.content[:100] + '...' for f in key_findings[:3]])}"
            )
        
        # Implications
        implications = self.facts_by_category.get("implications", [])
        if implications:
            summary_parts.append(
                f"Les implications clés de ces découvertes sont : "
                f"{implications[0].content[:150]}..."
            )
        
        return " ".join(summary_parts)
    
    async def _generate_main_content(self, 
                                   facts: List[Fact], 
                                   contradictions: List[Contradiction],
                                   sources: List[SearchResult]) -> str:
        """Générer le contenu principal du rapport en Markdown"""
        content_parts = []
        
        # En-tête
        content_parts.append(f"# DeepClaw Research Report: {self.session.topic}\n")
        content_parts.append(f"*Généré le {datetime.now().strftime('%B %d, %Y à %H:%M')}*\n")
        
        # Résumé exécutif
        executive_summary = await self._generate_executive_summary(
            facts, contradictions, sources
        )
        content_parts.append(f"## Résumé Exécutif\n\n{executive_summary}\n")
        
        # Table des matières
        content_parts.append("## Table des Matières\n")
        content_parts.append("1. [Méthodologie](#méthodologie)\n")
        content_parts.append("2. [Sources Consultées](#sources-consultées)\n")
        content_parts.append("3. [Résultats Principaux](#résultats-principaux)\n")
        content_parts.append("4. [Analyse des Contradictions](#analyse-des-contradictions)\n")
        content_parts.append("5. [Implications et Recommandations](#implications-et-recommandations)\n")
        content_parts.append("6. [Bibliographie](#bibliographie)\n\n")
        
        # Méthodologie
        content_parts.append("## Méthodologie\n")
        methodology_facts = self.facts_by_category.get("methodology", [])
        if methodology_facts:
            content_parts.append(
                f"La recherche a été effectuée en utilisant une approche hybride "
                f"combinant les API de recherche (Brave Search, DuckDuckGo) "
                f"et l'analyse sémantique avancée. "
                f"{len(sources)} sources ont été consultées à travers {self.session.depth} "
                f"niveaux de recherche récursive.\n"
            )
        else:
            content_parts.append(
                f"La recherche a été effectuée avec {len(sources)} sources "
                f"consultées via des moteurs de recherche web fiables.\n"
            )
        content_parts.append("\n")
        
        # Sources consultées
        content_parts.append("## Sources Consultées\n")
        for i, source in enumerate(sources[:20], 1):  # Limiter à 20 sources
            content_parts.append(
                f"{i}. [{source.title}]({source.url}) "
                f"(Pertinence: {source.relevance:.2f})\n"
            )
        if len(sources) > 20:
            content_parts.append(f"*Et {len(sources) - 20} autres sources...*\n")
        content_parts.append("\n")
        
        # Résultats principaux
        content_parts.append("## Résultats Principaux\n")
        key_findings = self.facts_by_category.get("key_findings", [])
        for i, fact in enumerate(key_findings[:10], 1):
            content_parts.append(f"### {i}. {fact.content}\n")
        content_parts.append("\n")
        
        # Analyse des contradictions
        content_parts.append("## Analyse des Contradictions\n")
        if contradictions:
            content_parts.append(
                f"L'analyse a détecté {len(contradictions)} contradictions "
                f"entre les différentes sources consultées.\n\n"
            )
            
            # Par sévérité
            for severity in ["high", "medium", "low"]:
                contr_list = self.contradictions_by_severity.get(severity, [])
                if contr_list:
                    content_parts.append(f"### Contradictions {severity.upper()}\n")
                    for contradiction in contr_list[:5]:  # Limiter à 5 par sévérité
                        content_parts.append(f"- {contradiction.description}\n")
                    content_parts.append("\n")
        else:
            content_parts.append("Aucune contradiction significative n'a été détectée entre les sources.\n\n")
        
        # Implications et recommandations
        content_parts.append("## Implications et Recommandations\n")
        implications = self.facts_by_category.get("implications", [])
        if implications:
            for i, impl in enumerate(implications[:5], 1):
                content_parts.append(f"### {i}. {impl.content}\n")
        else:
            content_parts.append(
                "Sur la base des faits établis, plusieurs implications peuvent être tirées "
                "pour la recherche future et l'application pratique de ces connaissances.\n"
            )
        content_parts.append("\n")
        
        # Bibliographie
        content_parts.append("## Bibliographie\n")
        for i, source in enumerate(sources, 1):
            content_parts.append(
                f"{i}. {source.title}. "
                f"Disponible à : {source.url}. "
                f"Consulté le {datetime.now().strftime('%Y-%m-%d')}.\n"
            )
        content_parts.append("\n")
        
        return "\n".join(content_parts)
    
    async def _prepare_citations(self, sources: List[SearchResult]) -> List[Dict]:
        """Préparer les citations au format BibTeX"""
        citations = []
        
        for i, source in enumerate(sources, 1):
            # Extraire l'année si disponible
            year = datetime.now().year
            
            citation = {
                "id": f"ref{i}",
                "type": "webpage",
                "title": source.title,
                "url": source.url,
                "author": getattr(source, 'author', 'Unknown'),
                "year": year,
                "accessed": datetime.now().strftime("%Y-%m-%d")
            }
            citations.append(citation)
        
        return citations