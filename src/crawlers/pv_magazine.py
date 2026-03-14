"""
Crawler for PV Magazine (https://www.pv-magazine.com)
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from .base import BaseCrawler


class PVMagazineCrawler(BaseCrawler):
    """Crawler for PV Magazine solar power news."""
    
    @property
    def source_url(self) -> str:
        return "https://www.pv-magazine.com"
    
    @property
    def source_display_name(self) -> str:
        return "PV Magazine"
    
    async def fetch_article_urls(self) -> List[str]:
        """Fetch article URLs from PV Magazine."""
        session = await self.get_session()
        urls = []
        
        try:
            # Start with main news page
            async with session.get(f"{self.source_url}/news/") as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Find article links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Filter for article URLs
                        if '/news/' in href and href.endswith('/'):
                            full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                            if full_url not in urls:
                                urls.append(full_url)
            
            logger.info(f"Found {len(urls)} potential articles from PV Magazine")
            return urls[:20]  # Limit to 20 articles
            
        except Exception as e:
            logger.error(f"Error fetching PV Magazine URLs: {e}")
            return []
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse a PV Magazine article."""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract title
                title_elem = soup.find('h1', class_=re.compile(r'title|headline'))
                if not title_elem:
                    title_elem = soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # Extract content
                content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'content|article-body'))
                content = ""
                if content_elem:
                    # Get text from paragraphs
                    paragraphs = content_elem.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # Extract author
                author_elem = soup.find('span', class_=re.compile(r'author|byline'))
                author = author_elem.get_text(strip=True) if author_elem else ""
                
                # Extract publish date
                date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|published'))
                publish_date = ""
                if date_elem:
                    publish_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                # Extract summary/excerpt
                summary_elem = soup.find('meta', attrs={'name': 'description'})
                summary = summary_elem.get('content', '') if summary_elem else ""
                
                # Generate article ID
                article_id = self.generate_article_id(url)
                
                # Create article structure
                article = self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author=author,
                    publish_date=publish_date,
                    content=content,
                    summary=summary,
                    keywords=self._extract_keywords(soup),
                    categories=self._extract_categories(soup),
                    raw_html=html[:10000]  # Store first 10k chars for debugging
                )
                
                return article
                
        except Exception as e:
            logger.error(f"Error parsing PV Magazine article {url}: {e}")
            return None
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from article metadata."""
        keywords = []
        
        # Check meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # Check OpenGraph tags
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'og:tag|article:tag')})
        for tag in og_tags:
            if tag.get('content'):
                keywords.append(tag['content'].strip())
        
        return list(set(keywords))
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract categories from article."""
        categories = []
        
        # Look for breadcrumbs or category links
        breadcrumbs = soup.find('nav', class_=re.compile(r'breadcrumb'))
        if breadcrumbs:
            for link in breadcrumbs.find_all('a'):
                text = link.get_text(strip=True)
                if text and text.lower() not in ['home', 'news']:
                    categories.append(text)
        
        # Look for category tags
        category_tags = soup.find_all('a', class_=re.compile(r'category|tag'))
        for tag in category_tags:
            text = tag.get_text(strip=True)
            if text and len(text) < 50:  # Avoid long text that might not be a category
                categories.append(text)
        
        return list(set(categories))


# Configure logger
import logging
logger = logging.getLogger(__name__)