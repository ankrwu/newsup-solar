"""
企业官网新闻爬虫基类
用于爬取光伏企业官网的新闻动态
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


async def _decode_response(response) -> str:
    """正确解码响应内容，处理各种编码"""
    try:
        content = await response.read()
        
        # 从 Content-Type 头获取编码
        content_type = response.headers.get('Content-Type', '')
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].strip()
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
        
        # 尝试常见编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 最后尝试忽略错误
        return content.decode('utf-8', errors='ignore')
        
    except Exception as e:
        logger.error(f"解码响应出错: {e}")
        return ""


class LongiCrawler(BaseCrawler):
    """隆基绿能官网爬虫"""
    
    @property
    def source_url(self) -> str:
        return "https://www.longi.com"
    
    @property
    def source_display_name(self) -> str:
        return "隆基绿能"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表"""
        article_urls = []
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/cn/news/",
            f"{self.source_url}/cn/media-center/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        for link in soup.select('a[href*="/news/"], a[href*=".html"]'):
                            href = link.get('href', '')
                            if href and '.html' in href:
                                full_url = self._normalize_url(href)
                                if full_url and full_url not in article_urls:
                                    article_urls.append(full_url)
                    else:
                        logger.warning(f"获取 {category_url} 失败: {response.status}")
            
            except Exception as e:
                logger.error(f"处理 {category_url} 时出错: {e}")
        
        logger.info(f"从隆基绿能总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:20]
    
    def _normalize_url(self, href: str) -> str:
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
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                publish_date = self._extract_date(soup)
                article_id = self.generate_article_id(url)
                
                return self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author="隆基绿能",
                    publish_date=publish_date,
                    content=content,
                    summary="",
                    keywords=["隆基", "光伏", "太阳能"],
                    categories=["企业新闻"],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'China',
                        'crawled_by': 'longi_crawler',
                        'source_type': 'company_official',
                    }
                )
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ['h1', '.news-title', '.title', 'title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*隆基.*$', '', title)
                return title
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        for selector in ['.news-content', '.content', '.article-content', 'article']:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(content) > 100:
                    return content[:5000]
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        text = soup.get_text()
        match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', text)
        if match:
            return match.group(1)
        return ""


class JASolarCrawler(BaseCrawler):
    """晶澳科技官网爬虫"""
    
    @property
    def source_url(self) -> str:
        return "https://www.jasolar.com"
    
    @property
    def source_display_name(self) -> str:
        return "晶澳科技"
    
    async def fetch_article_urls(self) -> List[str]:
        article_urls = []
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/cn/news/",
            f"{self.source_url}/cn/media/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        for link in soup.select('a[href*=".html"]'):
                            href = link.get('href', '')
                            if href:
                                full_url = self._normalize_url(href)
                                if full_url and full_url not in article_urls:
                                    article_urls.append(full_url)
            
            except Exception as e:
                logger.error(f"处理 {category_url} 时出错: {e}")
        
        logger.info(f"从晶澳科技总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:20]
    
    def _normalize_url(self, href: str) -> str:
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
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                publish_date = self._extract_date(soup)
                article_id = self.generate_article_id(url)
                
                return self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author="晶澳科技",
                    publish_date=publish_date,
                    content=content,
                    summary="",
                    keywords=["晶澳", "光伏", "太阳能"],
                    categories=["企业新闻"],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'China',
                        'crawled_by': 'jasolar_crawler',
                        'source_type': 'company_official',
                    }
                )
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ['h1', '.news-title', '.title', 'title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*晶澳.*$', '', title)
                return title
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        for selector in ['.news-content', '.content', '.article-content', 'article']:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(content) > 100:
                    return content[:5000]
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        text = soup.get_text()
        match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', text)
        if match:
            return match.group(1)
        return ""


class TrinaSolarCrawler(BaseCrawler):
    """天合光能官网爬虫"""
    
    @property
    def source_url(self) -> str:
        return "https://www.trinasolar.com"
    
    @property
    def source_display_name(self) -> str:
        return "天合光能"
    
    async def fetch_article_urls(self) -> List[str]:
        article_urls = []
        session = await self.get_session()
        
        category_urls = [
            f"{self.source_url}/cn/news/",
            f"{self.source_url}/cn/media-center/",
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        for link in soup.select('a[href*=".html"], a[href*="/news/"]'):
                            href = link.get('href', '')
                            if href:
                                full_url = self._normalize_url(href)
                                if full_url and full_url not in article_urls:
                                    article_urls.append(full_url)
            
            except Exception as e:
                logger.error(f"处理 {category_url} 时出错: {e}")
        
        logger.info(f"从天合光能总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:20]
    
    def _normalize_url(self, href: str) -> str:
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
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                publish_date = self._extract_date(soup)
                article_id = self.generate_article_id(url)
                
                return self.create_article_structure(
                    article_id=article_id,
                    title=title,
                    url=url,
                    author="天合光能",
                    publish_date=publish_date,
                    content=content,
                    summary="",
                    keywords=["天合光能", "光伏", "太阳能"],
                    categories=["企业新闻"],
                    raw_html=html[:10000],
                    metadata={
                        'language': 'zh',
                        'source_country': 'China',
                        'crawled_by': 'trinasolar_crawler',
                        'source_type': 'company_official',
                    }
                )
        
        except Exception as e:
            logger.error(f"解析文章 {url} 时出错: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ['h1', '.news-title', '.title', 'title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                title = re.sub(r'[-_]\s*天合.*$', '', title)
                return title
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        for selector in ['.news-content', '.content', '.article-content', 'article']:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(content) > 100:
                    return content[:5000]
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        text = soup.get_text()
        match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', text)
        if match:
            return match.group(1)
        return ""
