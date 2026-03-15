"""
低碳网 (www.ditan.com) 爬虫
低碳经济资讯门户，涵盖新能源、光伏、储能等领域
支持静态网页爬取
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class DiTanCrawler(BaseCrawler):
    """低碳网爬虫 - 低碳经济资讯门户"""
    
    @property
    def source_url(self) -> str:
        return "https://www.ditan.com"
    
    @property
    def source_display_name(self) -> str:
        return "低碳网"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表"""
        article_urls = []
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/",
            f"{self.source_url}/news/",
            f"{self.source_url}/solar/",
            f"{self.source_url}/newenergy/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        article_selectors = [
                            '.news-list a',
                            '.article-list a',
                            'a[href*=".html"]',
                            'h2 a',
                            'h3 a',
                        ]
                        
                        for selector in article_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = self._normalize_url(href)
                                    if full_url and full_url not in article_urls:
                                        article_urls.append(full_url)
                    else:
                        logger.warning(f"获取 {category_url} 失败: {response.status}")
            
            except Exception as e:
                logger.error(f"处理 {category_url} 时出错: {e}")
        
        logger.info(f"从低碳网总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:30]
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        excluded = [
            r'/list', r'/index', r'/search', r'#',
            r'\.pdf$', r'\.jpg$', r'\.png$',
            r'javascript:', r'mailto:',
        ]
        
        for pattern in excluded:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        article_patterns = [r'\.html$', r'/\d{4}/\d{2}/\d{2}/', r'/\d{8}/']
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _normalize_url(self, href: str) -> str:
        """规范化URL"""
        if not href:
            return ""
        
        if href.startswith('http://') or href.startswith('https://'):
            return href
        
        if href.startswith('//'):
            return f'https:{href}'
        
        if href.startswith('/'):
            return f"{self.source_url}{href}"
        
        return f"{self.source_url}/{href}"
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """解析文章内容"""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"获取文章 {url} 失败: {response.status}")
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
                        'crawled_by': 'ditan_crawler',
                        'source_type': 'industry_portal',
                    }
                )
                
                logger.debug(f"解析文章: {title}")
                return article
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1', '.article-title', '.title', 'title']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*低碳网.*$', '', title)
                return title
        
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content_selectors = ['.article-content', '.content', '.article-body', 'article']
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                for tag in elem(['script', 'style', 'iframe']):
                    tag.decompose()
                
                paragraphs = elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    content = re.sub(r'责任编辑.*$', '', content)
                    
                    if len(content) > 100:
                        return content
        
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True)])
        return content[:5000]
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者/来源"""
        selectors = ['.author', '.source', '.article-info span']
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                source_match = re.search(r'来源[：:]\s*(\S+)', text)
                if source_match:
                    return source_match.group(1)
                return text
        
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        text = soup.get_text()
        date_patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{4}-\d{2}-\d{2})',
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
