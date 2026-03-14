"""
Base crawler class for news sources.
"""

import abc
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class BaseCrawler(abc.ABC):
    """Abstract base class for news crawlers."""
    
    def __init__(self):
        self.source_name = self.__class__.__name__.replace("Crawler", "")
        self.base_url = ""
        self.session = None
    
    @property
    @abc.abstractmethod
    def source_url(self) -> str:
        """Return the base URL of the news source."""
        pass
    
    @property
    @abc.abstractmethod
    def source_display_name(self) -> str:
        """Return the display name of the news source."""
        pass
    
    @abc.abstractmethod
    async def fetch_article_urls(self) -> List[str]:
        """Fetch list of article URLs from the source."""
        pass
    
    @abc.abstractmethod
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse a single article and extract relevant information."""
        pass
    
    async def crawl(self) -> List[Dict[str, Any]]:
        """Main crawling method."""
        logger.info(f"Starting crawl for {self.source_display_name}")
        
        articles = []
        
        # Get article URLs
        try:
            urls = await self.fetch_article_urls()
            logger.info(f"Found {len(urls)} articles to crawl from {self.source_display_name}")
        except Exception as e:
            logger.error(f"Error fetching article URLs from {self.source_display_name}: {e}")
            return articles
        
        # Crawl each article
        for url in urls[:10]:  # Limit to 10 articles for initial testing
            try:
                article = await self.parse_article(url)
                if article:
                    articles.append(article)
                    logger.debug(f"Successfully parsed: {article.get('title', 'Unknown title')}")
            except Exception as e:
                logger.error(f"Error parsing article {url}: {e}")
        
        logger.info(f"Crawled {len(articles)} articles from {self.source_display_name}")
        return articles
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def generate_article_id(self, url: str) -> str:
        """Generate a unique ID for an article based on its URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def create_article_structure(self, **kwargs) -> Dict[str, Any]:
        """Create a standardized article structure."""
        now = datetime.utcnow().isoformat()
        
        return {
            "article_id": kwargs.get("article_id", ""),
            "title": kwargs.get("title", ""),
            "url": kwargs.get("url", ""),
            "source": self.source_display_name,
            "source_url": self.source_url,
            "author": kwargs.get("author", ""),
            "publish_date": kwargs.get("publish_date", now),
            "crawl_date": now,
            "content": kwargs.get("content", ""),
            "summary": kwargs.get("summary", ""),
            "keywords": kwargs.get("keywords", []),
            "categories": kwargs.get("categories", []),
            "sentiment_score": kwargs.get("sentiment_score", 0.0),
            "relevance_score": kwargs.get("relevance_score", 0.0),
            "metadata": kwargs.get("metadata", {}),
            "raw_html": kwargs.get("raw_html", ""),
            "processed": False,
            "processing_date": None,
        }
    
    def __del__(self):
        """Ensure session is closed on deletion."""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.session.close())