"""
光伏资讯 (solar.ofweek.com) 爬虫
OFweek 光伏网，光伏行业专业媒体，技术深度报道
支持静态网页爬取，使用 chardet 自动检测编码
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class OfweekSolarCrawler(BaseCrawler):
    """OFweek光伏网爬虫 - 光伏行业专业媒体"""
    
    @property
    def source_url(self) -> str:
        return "https://solar.ofweek.com"
    
    @property
    def source_display_name(self) -> str:
        return "OFweek光伏网"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表"""
        article_urls = []
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/",
            f"{self.source_url}/news/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await self._decode_response(response)
                        soup = BeautifulSoup(html, 'lxml')
                        
                        article_selectors = [
                            '.news-list a',
                            '.article-list a',
                            'a[href*=".html"]',
                            'h2 a', 'h3 a', '.title a',
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
        
        logger.info(f"从OFweek光伏网总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:30]
    
    async def _decode_response(self, response) -> str:
        """正确解码响应内容，使用 chardet 自动检测编码"""
        try:
            content = await response.read()
            
            if not content:
                return ""
            
            # 优先从 Content-Type 头获取编码
            content_type = response.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].strip().strip('"\'')
                try:
                    return content.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    pass
            
            # 使用 chardet 自动检测编码
            if CHARDET_AVAILABLE:
                detected = chardet.detect(content)
                encoding = detected.get('encoding', 'utf-8')
                confidence = detected.get('confidence', 0)
                
                if encoding and confidence > 0.7:
                    try:
                        decoded = content.decode(encoding)
                        logger.debug(f"chardet 检测编码: {encoding} (置信度: {confidence:.2f})")
                        return decoded
                    except (UnicodeDecodeError, LookupError):
                        pass
            
            # 回退：尝试常见中文编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']:
                try:
                    return content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 最后尝试忽略错误
            return content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.error(f"解码响应出错: {e}")
            return ""
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        excluded = [r'/list', r'/index', r'/search', r'#', r'\.pdf$', r'\.jpg$', 
                   r'\.png$', r'javascript:', r'mailto:', r'/tag/', r'/page/']
        
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
        if href.startswith('http'):
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
                
                html = await self._decode_response(response)
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                author = self._extract_author(soup)
                publish_date = self._extract_date(soup)
                summary = self._extract_summary(soup)
                keywords = self._extract_keywords(soup)
                article_id = self.generate_article_id(url)
                
                return self.create_article_structure(
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
                        'crawled_by': 'ofweek_solar_crawler',
                        'source_type': 'industry_media',
                    }
                )
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ['h1', '.article-title', '.title', 'title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*OFweek.*$', '', title, flags=re.IGNORECASE)
                return title
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        for selector in ['.article-content', '.content', '.article-body', 'article']:
            elem = soup.select_one(selector)
            if elem:
                for tag in elem(['script', 'style', 'iframe']):
                    tag.decompose()
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                content = re.sub(r'责任编辑.*$', '', content)
                if len(content) > 100:
                    return content[:5000]
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True)])
        return content[:5000]
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        for selector in ['.author', '.source', '.article-info span']:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                match = re.search(r'来源[：:]\s*(\S+)', text)
                if match:
                    return match.group(1)
                return text
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        text = soup.get_text()
        patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '') if meta else ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        keywords = []
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta and meta.get('content'):
            keywords = [k.strip() for k in meta['content'].split(',') if k.strip()]
        return keywords[:10]
