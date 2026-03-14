"""
北极星太阳能光伏网爬虫
抓取 https://guangfu.bjx.com.cn/ 的新闻
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class BjxGuangfuCrawler(BaseCrawler):
    """北极星太阳能光伏网爬虫"""
    
    @property
    def source_url(self) -> str:
        return "https://guangfu.bjx.com.cn"
    
    @property
    def source_display_name(self) -> str:
        return "北极星光伏网"
    
    @property
    def list_urls(self) -> List[str]:
        """新闻列表页URL"""
        return [
            f"{self.source_url}/news/",           # 行业资讯
            f"{self.source_url}/zs/",             # 招中标
            f"{self.source_url}/qy/",             # 企业新闻
            f"{self.source_url}/zhengce/",        # 政策法规
            f"{self.source_url}/hyyw/",           # 行业要闻
        ]
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表"""
        session = await self.get_session()
        all_urls = []
        
        for list_url in self.list_urls:
            try:
                logger.info(f"Fetching articles from {list_url}")
                async with session.get(list_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # 北极星网站文章链接通常在列表中
                        # 尝试多种选择器
                        link_selectors = [
                            '.list li a',
                            '.news-list a',
                            'ul.list a',
                            '.article-list a',
                            'a[href*="/news/"]',
                            'a[href*=".shtml"]',
                        ]
                        
                        for selector in link_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in all_urls:
                                        all_urls.append(full_url)
                    
                    else:
                        logger.warning(f"Failed to fetch {list_url}: {response.status}")
            
            except Exception as e:
                logger.error(f"Error fetching {list_url}: {e}")
        
        logger.info(f"Found {len(all_urls)} articles from 北极星光伏网")
        return list(set(all_urls))[:30]
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        # 排除非文章链接
        excluded = [
            r'/list',
            r'/index',
            r'/search',
            r'#',
            r'\.pdf$',
            r'javascript:',
        ]
        
        for pattern in excluded:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 北极星文章URL通常是 .shtml 结尾或包含特定路径
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
                
                # 提取标题
                title = self._extract_title(soup)
                
                # 提取内容
                content = self._extract_content(soup)
                
                # 提取作者/来源
                author = self._extract_author(soup)
                
                # 提取发布日期
                publish_date = self._extract_date(soup)
                
                # 提取摘要
                summary = self._extract_summary(soup)
                
                # 提取关键词
                keywords = self._extract_keywords(soup)
                
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
                    keywords=keywords,
                    categories=keywords[:3] if keywords else [],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'China',
                        'crawled_by': 'bjx_guangfu',
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
                # 清理标题中的网站名
                title = re.sub(r'_北极星太阳能光伏网.*$', '', title)
                title = re.sub(r'-北极星.*$', '', title)
                return title
        return "Unknown Title"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文"""
        selectors = [
            '.article-content',
            '.news-content',
            '.content',
            '#article',
            'article',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                # 清理内容
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
                # 提取来源信息
                match = re.search(r'来源[：:]\s*(\S+)', text)
                if match:
                    return match.group(1)
                return text
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取日期"""
        # 尝试多种日期格式
        text = soup.get_text()
        
        # 匹配常见日期格式
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
