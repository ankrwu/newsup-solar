"""
北极星太阳能光伏网爬虫
支持 RSS、静态爬取和 Playwright 动态渲染三种方式
"""

import re
import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler
from ..dynamic_crawler import DynamicContentCrawler, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)


class BjxGuangfuCrawler(BaseCrawler, DynamicContentCrawler):
    """北极星太阳能光伏网爬虫 - 支持 RSS、静态和动态爬取"""
    
    # RSS 源配置
    RSS_FEEDS = [
        {
            'url': 'https://guangfu.bjx.com.cn/rss.xml',
            'description': '北极星光伏网 RSS'
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
        return "https://guangfu.bjx.com.cn"
    
    @property
    def source_display_name(self) -> str:
        return "北极星光伏网"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表 - 优先级: RSS > 静态爬取 > Playwright降级"""
        article_urls = []
        
        # 方法1: 尝试 RSS 订阅
        try:
            logger.info("Trying RSS feeds for 北极星光伏网...")
            rss_urls = await self._fetch_from_rss()
            if rss_urls:
                logger.info(f"Found {len(rss_urls)} articles via RSS")
                return rss_urls[:30]
        except Exception as e:
            logger.warning(f"RSS fetch failed: {e}, trying next method")
        
        # 方法2: 静态网页爬取（先尝试，因为更快）
        logger.info("Trying static web scraping...")
        session = await self.get_session()
        
        list_urls = [
            f"{self.source_url}/news/",
            f"{self.source_url}/hyyw/",
        ]
        
        for list_url in list_urls:
            try:
                logger.info(f"Fetching articles from {list_url}")
                await asyncio.sleep(1)
                
                async with session.get(list_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        link_selectors = [
                            '.list li a',
                            '.news-list a',
                            'ul.list a',
                            '.article-list a',
                            'a[href*=".shtml"]',
                        ]
                        
                        for selector in link_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in article_urls:
                                        article_urls.append(full_url)
                    else:
                        logger.warning(f"Failed to fetch {list_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching {list_url}: {e}")
        
        # 如果静态爬取成功获取到文章，直接返回
        if article_urls:
            logger.info(f"Found {len(article_urls)} articles via static scraping")
            return list(set(article_urls))[:30]
        
        # 方法3: 静态爬取失败，自动降级到 Playwright
        if PLAYWRIGHT_AVAILABLE:
            logger.info("Static scraping found no articles, auto-enabling Playwright fallback...")
            try:
                dynamic_urls = await self._fetch_with_playwright()
                if dynamic_urls:
                    logger.info(f"Found {len(dynamic_urls)} articles via Playwright fallback")
                    return dynamic_urls[:30]
            except Exception as e:
                logger.error(f"Playwright fallback failed: {e}")
        else:
            logger.warning("Playwright not available for fallback")
        
        logger.info(f"Total articles found from 北极星光伏网: {len(article_urls)}")
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
            f"{self.source_url}/news/",
            f"{self.source_url}/hyyw/",
        ]
        
        for list_url in list_urls:
            try:
                # 使用 Playwright 获取动态渲染后的页面
                html = await self.scroll_page(list_url, scroll_times=2, wait_time=1000)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    
                    link_selectors = [
                        '.list li a',
                        '.news-list a',
                        'ul.list a',
                        '.article-list a',
                        'a[href*=".shtml"]',
                    ]
                    
                    for selector in link_selectors:
                        for link in soup.select(selector):
                            href = link.get('href', '')
                            if href and self._is_article_url(href):
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
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        excluded = [
            r'/list',
            r'/index',
            r'/search',
            r'#',
            r'\.pdf$',
            r'javascript:',
            r'/rss',
        ]
        
        for pattern in excluded:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        if re.search(r'\.shtml$', url):
            return True
        if re.search(r'/news/\d+', url):
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
                keywords = self._extract_keywords(soup)
                article_id = self.generate_article_id(url)
                
                article = self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author=author,
                    publish_date=publish_date,
                    content=content,
                    summary=summary,
                    keywords=keywords,
                    categories=keywords[:3] if keywords else [],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'China',
                        'crawled_by': 'bjx_guangfu_rss',
                    }
                )
                
                logger.debug(f"Parsed article: {title}")
                return article
        
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1', '.article-title', '.news-title', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'_北极星太阳能光伏网.*$', '', title)
                title = re.sub(r'-北极星.*$', '', title)
                return title
        return "Unknown Title"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文"""
        selectors = ['.article-content', '.news-content', '.content', '#article', 'article']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                content = re.sub(r'责任编辑.*$', '', content)
                content = re.sub(r'版权声明.*$', '', content, flags=re.IGNORECASE)
                if len(content) > 50:
                    return content
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者/来源"""
        selectors = ['.source', '.author', '.article-info span']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                match = re.search(r'来源[：:]\s*(\S+)', text)
                if match:
                    return match.group(1)
                return text
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取日期"""
        text = soup.get_text()
        patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'发布时间[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta:
            return meta.get('content', '')
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta and meta.get('content'):
            keywords = [k.strip() for k in meta['content'].split(',')]
        return keywords[:10]
