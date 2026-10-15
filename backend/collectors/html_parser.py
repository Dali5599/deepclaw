"""
DeepClaw HTML Parser - Cleans HTML and extracts readable text
"""
import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
try:
    import trafilatura
except ImportError:
    trafilatura = None

logger = logging.getLogger(__name__)


class HTMLParser:
    """Parseur HTML pour extraire le contenu lisible"""
    
    @staticmethod
    def clean_html_content(html_content: str, url: str = None) -> str:
        """
        Nettoyer le HTML pour extraire uniquement le texte lisible
        
        Args:
            html_content: Contenu HTML brut
            url: URL de la source (pour trafilatura)
            
        Returns:
            Texte lisible nettoyé
        """
        try:
            # Essayer d'abord avec trafilatura (meilleur pour articles/news)
            if trafilatura and html_content:
                text = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                    favor_recall=True
                )
                if text and len(text.strip()) > 100:
                    return text.strip()
        except Exception as e:
            logger.debug(f"Trafilatura failed: {e}")
        
        # Fallback sur BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Supprimer les éléments non pertinents
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                              'aside', 'advertisement', 'ads', 'sidebar',
                              'noscript', 'iframe', 'svg', 'canvas']):
                element.decompose()
            
            # Supprimer les éléments avec des classes/id de pubs, navigation, etc.
            for selector in [
                '.ad', '.ads', '.advertisement', '.popup', '.modal',
                '.navbar', '.navigation', '.menu', '.sidebar',
                '.cookie-banner', '.newsletter', '.social-share',
                '[id*="ad"]', '[class*="ad"]', '[id*="banner"]'
            ]:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extraire le texte
            text = soup.get_text()
            
            # Nettoyer les lignes vides et espaces excessifs
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"BeautifulSoup parsing failed: {e}")
            # Dernier recours : regex simple
            return re.sub(r'<[^>]+>', ' ', html_content)
    
    @staticmethod
    def extract_metadata(html_content: str) -> dict:
        """
        Extraire les métadonnées de base depuis le HTML
        
        Returns:
            Dict avec title, description, author, published_date, etc.
        """
        metadata = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Titre
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '').strip()
            
            # Open Graph
            og_title = soup.find('meta', property='og:title')
            if og_title:
                metadata['og_title'] = og_title.get('content', '').strip()
            
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                metadata['og_description'] = og_desc.get('content', '').strip()
            
            # Auteur
            author_tag = soup.find('meta', attrs={'name': 'author'})
            if author_tag:
                metadata['author'] = author_tag.get('content', '').strip()
            
            # Date de publication
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="pubdate"]',
                'meta[name="date"]',
                'time[datetime]'
            ]
            
            for selector in date_selectors:
                date_tag = soup.select_one(selector)
                if date_tag:
                    if date_tag.name == 'meta':
                        metadata['published_date'] = date_tag.get('content', '').strip()
                    elif date_tag.name == 'time':
                        metadata['published_date'] = date_tag.get('datetime', '').strip()
                    break
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
        
        return metadata


def clean_html_content(html_content: str, url: str = None) -> str:
    """
    Fonction utilitaire pour nettoyer le contenu HTML
    
    Args:
        html_content: Contenu HTML brut
        url: URL de la source (optionnel)
        
    Returns:
        Texte lisible nettoyé
    """
    return HTMLParser.clean_html_content(html_content, url)


def extract_metadata(html_content: str) -> dict:
    """
    Fonction utilitaire pour extraire les métadonnées
    
    Args:
        html_content: Contenu HTML brut
        
    Returns:
        Dict avec les métadonnées extraites
    """
    return HTMLParser.extract_metadata(html_content)