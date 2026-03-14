"""
PV Magazine 中文版爬虫
抓取 https://www.pv-magazine-china.com/ 的新闻
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class PVMagazineChinaCrawler(BaseCrawler):
    """PV Magazine 中文版爬虫"""
    
    @property
    def source_url(self) -> str:
        return "https://www.pv-magazine-china.com"
    
    @property
    def source_display_name(self) -> str:
        return "PV Magazine 中国"
    
    @property
    def category_urls(self) -> List[str]:
        """分类页面URL列表"""
        return [
            f"{self.source_url}/news/",           # 新闻
            f"{self.source_url}/markets-policy/", # 市场与政策
            f"{self.source_url}/manufacturing/",  # 制造
            f"{self.source_url}/technology/",     # 技术
            f"{self.source_url}/installations/",  # 设施
        ]
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表"""
        session = await self.get_session()
        all_urls = []
        
        for category_url in self.category_urls:
            try:
                logger.info(f"Fetching articles from {category_url}")
                await asyncio.sleep(1)  # 添加延迟避免被封
                
                async with session.get(category_url) as response:
                    logger.info(f"Response status for {category_url}: {response.status}")
                    
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # 查找文章链接
                        article_selectors = [
                            'article a',
                            '.post-title a',
                            '.entry-title a',
                            'h2 a',
                            'h3 a',
                            'a[href*="/news/"]',
                        ]
                        
                        found_count = 0
                        for selector in article_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in all_urls:
                                        all_urls.append(full_url)
                                        found_count += 1
                        
                        logger.info(f"Found {found_count} articles from {category_url}")
                    else:
                        logger.warning(f"Failed to fetch {category_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching {category_url}: {e}")
        
        logger.info(f"Total articles found from PV Magazine China: {len(all_urls)}")
        return list(set(all_urls))[:30]  # 限制30篇
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        # 排除非文章链接
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
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 文章URL通常包含日期或特定路径
        article_patterns = [
            r'/\d{4}/\d{2}/',          # 包含日期 /2026/03/
            r'/news/\d',                # /news/xxx
            r'/markets-policy/\d',
            r'/manufacturing/\d',
            r'/technology/\d',
            r'/installations/\d',
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
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
                
                # 提取标题
                title = self._extract_title(soup)
                
                # 提取内容
                content = self._extract_content(soup)
                
                # 提取作者
                author = self._extract_author(soup)
                
                # 提取发布日期
                publish_date = self._extract_date(soup)
                
                # 提取摘要
                summary = self._extract_summary(soup)
                
                # 提取标签/分类
                tags = self._extract_tags(soup)
                
                # 生成文章ID
                article_id = self.generate_article_id(url)
                
                # 创建文章结构
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
                        'source_country': 'China',
                        'crawled_by': 'pv_magazine_china',
                    }
                )
                
                logger.debug(f"Parsed Chinese article: {title}")
                return article
        
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种选择器
        selectors = [
            ('h1', {}),
            ('h1.entry-title', {}),
            ('h1.article-title', {}),
            ('.post-title', {}),
            ('title', {}),
        ]
        
        for selector, attrs in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return "Unknown Title"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 尝试多种内容容器选择器
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
                # 提取所有段落
                paragraphs = elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 50:
                        return content
        
        # 备用：提取所有段落
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])
        return content
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        selectors = [
            '.author-name',
            '.byline',
            '.post-author',
            '[rel="author"]',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        # 尝试 time 元素
        time_elem = soup.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return datetime_attr
            return time_elem.get_text(strip=True)
        
        # 尝试 meta 标签
        meta_date = soup.find('meta', attrs={'property': 'article:published_time'})
        if meta_date:
            return meta_date.get('content', '')
        
        # 尝试其他日期元素
        date_selectors = ['.post-date', '.entry-date', '.published']
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        # 尝试 meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        # 尝试 og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '')
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签"""
        tags = []
        
        # 从 meta keywords 提取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            tags.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # 从标签区域提取
        tag_elems = soup.select('.tags a, .post-tags a, [rel="tag"]')
        for elem in tag_elems:
            tag_text = elem.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        return list(set(tags))[:10]
