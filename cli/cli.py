"""
DeepClaw CLI - Interface en ligne de commande pour lancer des recherches
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core import settings
from backend.db import init_db, get_async_session
from backend.db.models import Session as ResearchSession
from backend.collectors.web_collector import WebCollector
from backend.processors.fact_extractor import FactExtractor
from backend.processors.contradiction_detector import ContradictionDetector
from backend.processors.synthesizer import FactSynthesizer
from backend.pdf_generator import generate_pdf_from_html

logger = logging.getLogger(__name__)


async def run_research(topic: str, 
                      depth: int = 3, 
                      output_dir: str = "./reports",
                      generate_pdf: bool = True) -> dict:
    """
    Lancer une recherche complète via la CLI
    
    Args:
        topic: Sujet de recherche
        depth: Profondeur de recherche (1-5)
        output_dir: Répertoire de sortie pour les rapports
        generate_pdf: Générer un PDF en plus du Markdown
        
    Returns:
        Dictionnaire avec les résultats de la recherche
    """
    # Initialiser la base de données
    await init_db()
    
    # Créer une session de recherche
    async with get_async_session() as db_session:
        research_session = ResearchSession(
            topic=topic,
            depth=depth,
            max_sources=10
        )
        db_session.add(research_session)
        await db_session.commit()
        await db_session.refresh(research_session)
        
        logger.info(f"Session de recherche créée : {research_session.id}")
        
        # 1. Collecte des sources
        collector = WebCollector(settings.__dict__)
        await collector.initialize()
        
        try:
            search_results = await collector.search(topic, max_results=10)
            sources = []
            for result in search_results:
                source = ResearchSession.Source(
                    session_id=research_session.id,
                    url=result.url,
                    title=result.title,
                    content=result.content,
                    source_type=result.source_type,
                    relevance_score=result.relevance
                )
                db_session.add(source)
                sources.append(source)
            
            await db_session.commit()
            logger.info(f"Collecté {len(sources)} sources")
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des sources : {e}")
            raise
        finally:
            await collector.close()
        
        # 2. Extraction des faits
        extractor = FactExtractor(research_session)
        facts = []
        for source in sources:
            source_facts = await extractor.extract_from_source(source)
            facts.extend(source_facts)
        
        # Sauvegarder les faits
        for fact in facts:
            db_session.add(fact)
        await db_session.commit()
        logger.info(f"Extrait {len(facts)} faits")
        
        # 3. Détection des contradictions
        detector = ContradictionDetector(research_session)
        contradictions = await detector.detect_contradictions(facts)
        
        # Sauvegarder les contradictions
        for contradiction in contradictions:
            db_session.add(contradiction)
        await db_session.commit()
        logger.info(f"Détecté {len(contradictions)} contradictions")
        
        # 4. Synthèse du rapport
        synthesizer = FactSynthesizer(research_session)
        report = await synthesizer.synthesize_report(facts, contradictions, search_results)
        
        # Sauvegarder le rapport
        db_session.add(report)
        await db_session.commit()
        logger.info(f"Rapport généré : {report.id}")
        
        # 5. Génération des fichiers de sortie
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Générer le fichier Markdown
        md_file = output_path / f"{research_session.id}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report.content)
        
        # Générer le PDF si demandé
        pdf_file = None
        if generate_pdf:
            pdf_file = output_path / f"{research_session.id}.pdf"
            html_content = _markdown_to_html(report.content, research_session.topic)
            success = generate_pdf_from_html(
                html_content, 
                str(pdf_file), 
                title=research_session.topic
            )
            if not success:
                logger.warning("Échec de la génération du PDF")
                pdf_file = None
        
        return {
            "session_id": research_session.id,
            "topic": topic,
            "sources_collected": len(sources),
            "facts_extracted": len(facts),
            "contradictions_detected": len(contradictions),
            "markdown_file": str(md_file),
            "pdf_file": str(pdf_file) if pdf_file else None,
            "report": report
        }


def _markdown_to_html(markdown_content: str, title: str) -> str:
    """
    Convertir du Markdown simple en HTML pour la génération PDF
    
    Args:
        markdown_content: Contenu Markdown
        title: Titre du document
        
    Returns:
        Contenu HTML
    """
    # Conversion basique Markdown -> HTML
    # Dans une implémentation réelle, utiliser une bibliothèque comme markdown2 ou mistune
    html = f"<h1>{title}</h1>\n"
    
    lines = markdown_content.split('\n')
    for line in lines:
        if line.startswith('# '):
            html += f"<h1>{line[2:]}</h1>\n"
        elif line.startswith('## '):
            html += f"<h2>{line[3:]}</h2>\n"
        elif line.startswith('### '):
            html += f"<h3>{line[4:]}</h3>\n"
        elif line.startswith('- ') or line.startswith('* '):
            html += f"<ul><li>{line[2:]}</li></ul>\n"
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
            html += f"<ol><li>{line[3:]}</li></ol>\n"
        elif line.strip() == '':
            html += "<br>\n"
        else:
            html += f"<p>{line}</p>\n"
    
    return html


def main():
    """Point d'entrée de la CLI"""
    parser = argparse.ArgumentParser(
        description="DeepClaw - Autonomous Deep Research & Fact-Synthesis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  deepclaw "Intelligence Artificielle en 2024" --depth 3 --pdf
  deepclaw "Changement climatique" --depth 2 --output ./custom_reports/
        """
    )
    
    parser.add_argument(
        "topic",
        type=str,
        help="Sujet de recherche à analyser"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Profondeur de recherche (1-5, défaut: 3)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./reports",
        help="Répertoire de sortie pour les rapports (défaut: ./reports)"
    )
    
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Générer un PDF en plus du fichier Markdown"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activer le logging verbose"
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Lancer la recherche
    try:
        result = asyncio.run(run_research(
            topic=args.topic,
            depth=args.depth,
            output_dir=args.output,
            generate_pdf=args.pdf
        ))
        
        print("\n" + "="*60)
        print("✅ Recherche terminée avec succès !")
        print("="*60)
        print(f"Sujet : {result['topic']}")
        print(f"ID de session : {result['session_id']}")
        print(f"Sources collectées : {result['sources_collected']}")
        print(f"Faits extraits : {result['facts_extracted']}")
        print(f"Contradictions détectées : {result['contradictions_detected']}")
        print(f"Fichier Markdown : {result['markdown_file']}")
        if result['pdf_file']:
            print(f"Fichier PDF : {result['pdf_file']}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n❌ Recherche interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur lors de la recherche : {e}")
        print(f"\n❌ Erreur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()