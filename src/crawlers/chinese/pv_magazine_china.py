"""
PV Magazine 中文版爬虫
支持 RSS 和网页爬取两种方式
"""

import re
import logging
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class PVMagazineChinaCrawler(BaseCrawler):
    """PV Magazine 中文版爬虫 - 支持 RSS 和网页爬取"""
    
    # RSS 源配置
    RSS_FEEDS = [
        {
            'url': 'https://www.pv-magazine.com/feed/',
            'language': 'en',
            'description': 'PV Magazine Global RSS Feed'
        },
        {
            'url': 'https://www.pv-magazine.com/category/markets-policy/feed/',
            'language': 'en',
            'description': 'PV Magazine Markets & Policy'
        },
        {
            'url': 'https://www.pv-magazine.com/category/technology/feed/',
            'language': 'en',
            'description': 'PV Magazine Technology',
        },
    ]
    
    @property
    def source_url(self) -> str:
        return "https://www.pv-magazine-china.com"
    
    @property
    def source_display_name(self) -> str:
        return "PV Magazine 中国"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表 - 优先使用 RSS"""
        article_urls = []
        
        # 方法1: 尝试 RSS 论阅
        try:
            logger.info("Trying RSS feeds for PV Magazine...")
            rss_urls = await self._fetch_from_rss()
            if rss_urls:
                logger.info(f"Found {len(rss_urls)} articles via RSS")
                return rss_urls[:30]
        except Exception as e:
            logger.warning(f"RSS fetch failed: {e}, falling back to web scraping")
        
        # 方法2: 回退到网页爬取
        logger.info("Falling back to web scraping...")
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/news/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"Fetching articles from {category_url}")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        article_selectors = [
                            'article a',
                            '.post-title a',
                            '.entry-title a',
                            'h2 a',
                            'h3 a',
                        ]
                        
                        for selector in article_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in article_urls:
                                        article_urls.append(full_url)
                    else:
                        logger.warning(f"Failed to fetch {category_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching {category_url}: {e}")
        
        logger.info(f"Total articles found from PV Magazine China: {len(article_urls)}")
        return list(set(article_urls))[:30]
    
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
                        
                        # 解析 RSS XML
                        urls = self._parse_rss_xml(content)
                        all_urls.extend(urls)
                        logger.info(f"Found {len(urls)} articles from {feed_info['description']}")
                    else:
                        logger.warning(f"Failed to fetch RSS {rss_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching RSS {feed_info['url']}: {e}")
        
        return list(set(all_urls))[:30]
    
    def _parse_rss_xml(self, xml_content: str) -> List[str]:
        """解析 RSS XML 内容"""
        urls = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for item in root.findall('.//item'):
                link_elem = item.find('link')
                if link_elem is not None:
                    url = link_elem.text
                    if url and url not in urls:
                        urls.append(url)
        
        except ET.ParseError as e:
            logger.error(f"Error parsing RSS XML: {e}")
        
        return urls
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        excluded_patterns = [
            r'/author/',
            r'/category/',
            r'/tag/',
            r'/page/',
            r'#',
            r'\.pdf$',
            r'\.jpg$',
            r'\.png$',
            r'mailto:',
            r'javascript:',
            r'/feed/',
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 文章URL必须包含日期
        if re.search(r'/\d{4}/\d{2}/', url):
            return True
        if re.search(r'/news/\d', url):
            return True
        
        return False
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """解析文章内容"""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                author = self._extract_author(soup)
                publish_date = self._extract_date(soup)
                summary = self._extract_summary(soup)
                tags = self._extract_tags(soup)
                article_id = self.generate_article_id(url)
                
                article = self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author=author,
                    publish_date=publish_date,
                    content=content,
                    summary=summary,
                    keywords=tags,
                    categories=tags[:3] if tags else [],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'Global',
                        'crawled_by': 'pv_magazine_china_rss',
                    }
                )
                
                logger.debug(f"Parsed article: {title}")
                return article
        
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1', 'h1.entry-title', 'h1.article-title', '.post-title', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                # 清理标题
                title = re.sub(r'\s*[-|–]\s*PV Magazine.*$', '', title)
                title = re.sub(r'\s*[-|–]\s*pv magazine.*$', '', title, flags=re.IGNORECASE)
                return title
        return "Unknown Title"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content_selectors = [
            'article .entry-content',
            'article .article-content',
            '.post-content',
            '.article-body',
            'article',
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 50:
                        return content
        
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])
        return content
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        selectors = ['.author-name', '.byline', '.post-author', '[rel="author"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        time_elem = soup.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return datetime_attr
            return time_elem.get_text(strip=True)
        
        meta_date = soup.find('meta', attrs={'property': 'article:published_time'})
        if meta_date:
            return meta_date.get('content', '')
        
        date_selectors = ['.post-date', '.entry-date', '.published']
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '')
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签"""
        tags = []
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            tags.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        tag_elems = soup.select('.tags a, .post-tags a, [rel="tag"]')
        for elem in tag_elems:
            tag_text = elem.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        return list(set(tags))[:10]
