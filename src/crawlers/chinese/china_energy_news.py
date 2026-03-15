"""
中国能源报 (paper.people.com.cn/zgnyb/) 爬虫
人民日报社主管的能源行业权威媒体
使用 Playwright 动态渲染绕过访问限制
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler
from ..dynamic_crawler import DynamicContentCrawler, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)


class ChinaEnergyNewsCrawler(BaseCrawler, DynamicContentCrawler):
    """中国能源报爬虫 - 人民日报社主管能源媒体"""
    
    def __init__(self, use_playwright: bool = True):
        """
        初始化爬虫
        
        Args:
            use_playwright: 是否使用 Playwright 动态渲染（默认开启）
        """
        BaseCrawler.__init__(self)
        DynamicContentCrawler.__init__(self, headless=True, ignore_ssl=True)
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
    
    @property
    def source_url(self) -> str:
        return "https://paper.people.com.cn/zgnyb"
    
    @property
    def source_display_name(self) -> str:
        return "中国能源报"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表 - 使用 Playwright 绕过访问限制"""
        article_urls = []
        
        if self.use_playwright and PLAYWRIGHT_AVAILABLE:
            logger.info("使用 Playwright 获取中国能源报文章...")
            article_urls = await self._fetch_with_playwright()
            if article_urls:
                logger.info(f"通过 Playwright 找到 {len(article_urls)} 篇文章")
                return article_urls[:30]
        else:
            logger.warning("中国能源报需要 Playwright 支持，请安装 playwright")
        
        return article_urls
    
    async def _fetch_with_playwright(self) -> List[str]:
        """使用 Playwright 动态渲染获取文章链接"""
        article_urls = []
        
        # 人民网报纸电子版页面结构
        category_urls = [
            f"{self.source_url}/pc/layout/index.html",  # 首页
            f"{self.source_url}/pc/content/2026-03/15/content_1.html",  # 当期报纸
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"Playwright 获取: {category_url}")
                html = await self.scroll_page(category_url, scroll_times=2, wait_time=3000)
                
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # 人民网报纸页面的文章链接选择器
                    article_selectors = [
                        'a[href*="content"]',
                        '.news-list a',
                        '.article-list a',
                        '.list a',
                        'a[href*=".html"]',
                        '.paper-list a',
                        '.page-list a',
                    ]
                    
                    for selector in article_selectors:
                        for link in soup.select(selector):
                            href = link.get('href', '')
                            if href:
                                full_url = self._normalize_url(href, category_url)
                                if full_url and self._is_article_url(full_url) and full_url not in article_urls:
                                    article_urls.append(full_url)
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Playwright 获取 {category_url} 时出错: {e}")
        
        return article_urls
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        excluded = [
            r'/list',
            r'/index$',
            r'/search',
            r'#',
            r'\.pdf$',
            r'\.jpg$',
            r'\.png$',
            r'javascript:',
            r'mailto:',
            r'/tag/',
            r'/page/\d+$',
        ]
        
        for pattern in excluded:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        article_patterns = [
            r'/content/\d{4}-\d{2}/',
            r'/content_\d+\.html',
            r'\.html$',
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _normalize_url(self, href: str, base_url: str = "") -> str:
        """规范化URL"""
        if not href:
            return ""
        
        # 处理相对路径 ../../../content/ 这种格式
        if href.startswith('../'):
            # 解析相对路径
            parts = href.split('/')
            up_count = sum(1 for p in parts if p == '..')
            actual_path = '/'.join(p for p in parts if p != '..')
            
            # 从 base_url 向上回溯
            if base_url:
                base_parts = base_url.split('/')
                # 移除最后的文件名
                base_parts = base_parts[:-1]
                # 向上回溯
                for _ in range(up_count):
                    if base_parts:
                        base_parts.pop()
                return '/'.join(base_parts) + '/' + actual_path
            return f"https://paper.people.com.cn/{actual_path}"
        
        if href.startswith('http://') or href.startswith('https://'):
            return href
        
        if href.startswith('//'):
            return f'https:{href}'
        
        if href.startswith('/'):
            return f"https://paper.people.com.cn{href}"
        
        # 相对路径，使用基础URL
        if base_url:
            base = base_url.rsplit('/', 1)[0]
            return f"{base}/{href}"
        
        return f"{self.source_url}/{href}"
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """解析文章内容"""
        html = None
        
        # 使用 Playwright 解析
        if self.use_playwright and PLAYWRIGHT_AVAILABLE:
            try:
                html = await self.fetch_page(url, wait_time=3000)
            except Exception as e:
                logger.warning(f"Playwright 解析 {url} 失败: {e}")
        
        if not html:
            return None
        
        try:
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
                raw_html=html[:10000] if html else "",
                metadata={
                    'language': 'zh',
                    'source_country': 'China',
                    'crawled_by': 'china_energy_news_crawler',
                    'source_type': 'official_media',
                }
            )
            
            logger.debug(f"解析文章: {title}")
            return article
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1', '.article-title', '.news-title', '.title', '#title', 'title']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*中国能源报.*$', '', title)
                title = re.sub(r'[-_]\s*人民网.*$', '', title)
                return title
        
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content_selectors = [
            '#content_body',
            '.article-content',
            '.news-content',
            '.content',
            '.article-body',
            '#ozoom',
            'article',
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                for tag in elem(['script', 'style', 'iframe', 'ins']):
                    tag.decompose()
                
                paragraphs = elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    content = re.sub(r'责任编辑.*$', '', content)
                    content = re.sub(r'来源.*$', '', content)
                    
                    if len(content) > 100:
                        return content[:5000]
        
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True)])
        return content[:5000]
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者/来源"""
        selectors = ['.author', '.source', '.article-info span', '.editor']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                author_match = re.search(r'作者[：:]\s*(\S+)', text)
                if author_match:
                    return author_match.group(1)
                
                source_match = re.search(r'来源[：:]\s*(\S+)', text)
                if source_match:
                    return source_match.group(1)
                
                return text
        
        return "中国能源报"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        text = soup.get_text()
        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}/\d{2}/\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords['content'].split(',') if k.strip()]
        
        return keywords[:10]
