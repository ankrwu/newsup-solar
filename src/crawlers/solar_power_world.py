"""
Crawler for Solar Power World (https://www.solarpowerworldonline.com)
支持 RSS、静态爬取和 Playwright 动态渲染
"""

import re
import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .base import BaseCrawler
from .dynamic_crawler import DynamicContentCrawler, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)


class SolarPowerWorldCrawler(BaseCrawler, DynamicContentCrawler):
    """Crawler for Solar Power World news - 支持 RSS、静态和动态爬取"""
    
    # RSS 源配置
    RSS_FEEDS = [
        {
            'url': 'https://www.solarpowerworldonline.com/feed/',
            'description': 'Solar Power World RSS Feed'
        },
        {
            'url': 'https://www.solarpowerworldonline.com/category/news/feed/',
            'description': 'Solar Power World News'
        },
        {
            'url': 'https://www.solarpowerworldonline.com/category/commercial-solar/feed/',
            'description': 'Solar Power World Commercial Solar'
        },
    ]
    
    def __init__(self, use_playwright: bool = False):
        """
        初始化爬虫
        
        Args:
            use_playwright: 是否使用 Playwright 进行动态渲染
        """
        BaseCrawler.__init__(self)
        DynamicContentCrawler.__init__(self, headless=True)
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
    
    @property
    def source_url(self) -> str:
        return "https://www.solarpowerworldonline.com"
    
    @property
    def source_display_name(self) -> str:
        return "Solar Power World"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表 - 优先级: RSS > 动态渲染 > 静态爬取"""
        article_urls = []
        
        # 方法1: 尝试 RSS 订阅
        try:
            logger.info("Trying RSS feeds for Solar Power World...")
            rss_urls = await self._fetch_from_rss()
            if rss_urls:
                logger.info(f"Found {len(rss_urls)} articles via RSS")
                return rss_urls[:30]
        except Exception as e:
            logger.warning(f"RSS fetch failed: {e}, trying next method")
        
        # 方法2: 尝试 Playwright 动态渲染
        if self.use_playwright and self.is_available:
            try:
                logger.info("Trying Playwright for dynamic content...")
                dynamic_urls = await self._fetch_with_playwright()
                if dynamic_urls:
                    logger.info(f"Found {len(dynamic_urls)} articles via Playwright")
                    return dynamic_urls[:30]
            except Exception as e:
                logger.warning(f"Playwright fetch failed: {e}, falling back to static")
        
        # 方法3: 静态网页爬取
        logger.info("Falling back to static web scraping...")
        session = await self.get_session()
        
        try:
            async with session.get(f"{self.source_url}/category/news/") as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    article_links = soup.select('article a, .post-title a, .entry-title a')
                    
                    for link in article_links:
                        href = link.get('href', '')
                        if href and ('/news/' in href or '/article/' in href):
                            full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                            if full_url not in article_urls:
                                article_urls.append(full_url)
            
            logger.info(f"Found {len(article_urls)} articles from static scraping")
            return article_urls[:15]
            
        except Exception as e:
            logger.error(f"Error fetching Solar Power World URLs: {e}")
            return []
    
    async def _fetch_from_rss(self) -> List[str]:
        """从 RSS 源获取文章 URL"""
        session = await self.get_session()
        all_urls = []
        
        for feed_info in self.RSS_FEEDS:
            try:
                rss_url = feed_info['url']
                logger.info(f"Fetching RSS from {rss_url}")
                
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        urls = self._parse_rss_xml(content)
                        all_urls.extend(urls)
                        logger.info(f"Found {len(urls)} articles from {feed_info['description']}")
                    else:
                        logger.warning(f"Failed to fetch RSS {rss_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching RSS {feed_info['url']}: {e}")
        
        return list(set(all_urls))
    
    async def _fetch_with_playwright(self) -> List[str]:
        """使用 Playwright 动态渲染获取文章链接"""
        article_urls = []
        
        list_urls = [
            f"{self.source_url}/category/news/",
            f"{self.source_url}/category/commercial-solar/",
        ]
        
        for list_url in list_urls:
            try:
                html = await self.scroll_page(list_url, scroll_times=2, wait_time=1000)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    
                    article_links = soup.select('article a, .post-title a, .entry-title a')
                    
                    for link in article_links:
                        href = link.get('href', '')
                        if href and ('/news/' in href or '/article/' in href):
                            full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                            if full_url not in article_urls:
                                article_urls.append(full_url)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error with Playwright on {list_url}: {e}")
        
        return article_urls
    
    def _parse_rss_xml(self, xml_content: str) -> List[str]:
        """解析 RSS XML 内容"""
        urls = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for item in root.findall('.//item'):
                link_elem = item.find('link')
                if link_elem is not None and link_elem.text:
                    urls.append(link_elem.text)
        
        except ET.ParseError as e:
            logger.error(f"Error parsing RSS XML: {e}")
        
        return urls
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse a Solar Power World article."""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract title
                title_elem = soup.find('h1', class_=re.compile(r'title|entry-title|post-title'))
                if not title_elem:
                    title_elem = soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # Extract content
                content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'entry-content|article-content|post-content'))
                content = ""
                if content_elem:
                    paragraphs = content_elem.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # Extract author
                author_elem = soup.find('span', class_=re.compile(r'author|byline'))
                author = author_elem.get_text(strip=True) if author_elem else ""
                
                # Extract publish date
                date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|posted-on'))
                publish_date = ""
                if date_elem:
                    publish_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                # Extract summary
                summary_elem = soup.find('meta', attrs={'property': 'og:description'})
                if not summary_elem:
                    summary_elem = soup.find('meta', attrs={'name': 'description'})
                summary = summary_elem.get('content', '') if summary_elem else ""
                
                # Generate article ID
                article_id = self.generate_article_id(url)
                
                # Extract categories/tags
                categories = []
                tags_section = soup.find('div', class_=re.compile(r'tags|categories'))
                if tags_section:
                    for tag in tags_section.find_all('a'):
                        categories.append(tag.get_text(strip=True))
                
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
                    categories=categories,
                    raw_html=html[:8000]
                )
                
                return article
                
        except Exception as e:
            logger.error(f"Error parsing Solar Power World article {url}: {e}")
            return None
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from article metadata."""
        keywords = []
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        tag_elements = soup.find_all('a', class_=re.compile(r'tag|keyword'))
        for tag in tag_elements:
            text = tag.get_text(strip=True)
            if text:
                keywords.append(text)
        
        solar_terms = [
            'solar', 'photovoltaic', 'PV', 'renewable', 'clean energy',
            'solar panel', 'solar installation', 'solar farm', 'solar project',
            'solar power', 'solar energy', 'rooftop solar', 'utility-scale'
        ]
        
        content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'content'))
        if content_elem:
            content_text = content_elem.get_text().lower()
            for term in solar_terms:
                if term.lower() in content_text:
                    keywords.append(term)
        
        return list(set([k for k in keywords if k]))
