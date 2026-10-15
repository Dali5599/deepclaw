"""
DeepClaw PDF Generator - Génération de PDF via Playwright
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from ..core import settings

logger = logging.getLogger(__name__)


def generate_pdf_from_html(html_content: str, 
                          output_path: str,
                          title: str = "DeepClaw Research Report") -> bool:
    """
    Générer un PDF à partir de contenu HTML via Playwright
    
    Args:
        html_content: Contenu HTML à convertir en PDF
        output_path: Chemin de sortie pour le PDF
        title: Titre du document (utilisé pour les métadonnées)
        
    Returns:
        True si le PDF a été généré avec succès, False sinon
    """
    try:
        # Importation différée pour éviter les dépendances inutiles
        import sys
        from playwright.async_api import async_playwright
        
        # Préparer le HTML avec un style imprimable professionnel
        html_content = _prepare_html_for_pdf(html_content, title)
        
        # Lancer Playwright et générer le PDF
        async def generate():
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
                
                page = await browser.new_page()
                
                # Définir le contenu HTML de la page
                await page.set_content(html_content, wait_until="networkidle")
                
                # Obtenir les dimensions de la page (formater A4)
                await page.emulate_media(media="print")
                
                # Générer le PDF avec des options professionnelles
                pdf_bytes = await page.pdf(
                    path=output_path,
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        "top": "2cm",
                        "right": "2cm",
                        "bottom": "2cm",
                        "left": "2cm"
                    },
                    page_ranges="1",  # Toute la page
                    display_header_footer=False,
                    header_template="<div></div>",
                    footer_template="<div></div>",
                    scale=1.0
                )
                
                await browser.close()
                return True, None
        
        # Exécuter dans un thread séparé pour éviter le blocage
        import concurrent.futures
        import threading
        
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(generate())
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_thread)
            success, error = future.result(timeout=300)  # 5 minutes timeout
            
            if success:
                logger.info(f"PDF généré avec succès : {output_path}")
                return True
            else:
                logger.error(f"Erreur de génération de PDF : {error}")
                return False
                
    except Exception as e:
        logger.error(f"Exception lors de la génération de PDF : {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def _prepare_html_for_pdf(self, html_content: str, title: str) -> str:
    """
    Préparer le HTML pour la génération de PDF avec des styles professionnels
    
    Args:
        html_content: Contenu HTML original
        title: Titre du document
        
    Returns:
        HTML amélioré pour la génération de PDF
    """
    # Configuration des métadonnées du document
    metadata = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            /* Reset et styles de base */
            @page {{
                margin: 2cm;
                @bottom-center {{
                    content: "Page " counter(page) " sur " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: "Helvetica Neue", Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            
            .header {{
                text-align: center;
                border-bottom: 2px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            
            .title {{
                font-size: 24pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                font-size: 12pt;
                color: #666;
                font-style: italic;
            }}
            
            .section {{
                margin: 30px 0;
            }}
            
            .section-title {{
                font-size: 16pt;
                font-weight: bold;
                color: #2c3e50;
                border-bottom: 1px solid #3498db;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            
            .fact-item {{
                background-color: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 10px 0;
            }}
            
            .contradiction-item {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 10px 0;
            }}
            
            .citation {{
                font-family: "Courier New", monospace;
                background-color: #f8f9fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-size: 9pt;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            .footer {{
                text-align: center;
                font-size: 10pt;
                color: #999;
                margin-top: 50px;
                border-top: 1px solid #eee;
                padding-top: 20px;
            }}
            
            /* Améliorations pour l'impression */
            @media print {{
                body {{
                    font-size: 10pt;
                    line-height: 1.4;
                }}
                
                .no-print {{
                    display: none;
                }}
                
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Rechercher et remplacer les en-têtes/bas de page si présents dans le contenu original
    if "<header>" in html_content:
        metadata += html_content.replace("<header>", "<div class='header'>")
        metadata += html_content.replace("<footer>", "<div class='footer'>")
    else:
        metadata += html_content
    
    return metadata