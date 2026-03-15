"""
索比光伏网 (solarbe.com) 爬虫
中国最大的光伏门户网站，内容丰富，技术前沿
支持 RSS 和静态网页爬取
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


class SolarBECrawler(BaseCrawler):
    """索比光伏网爬虫"""
    
    # RSS 源配置（需要验证是否存在）
    RSS_FEEDS = [
        {
            'url': 'https://www.solarbe.com/rss',
            'description': '索比光伏网 RSS'
        },
        {
            'url': 'https://www.solarbe.com/feed',
            'description': '索比光伏网 Feed'
        },
    ]
    
    @property
    def source_url(self) -> str:
        return "https://www.solarbe.com"
    
    @property
    def source_display_name(self) -> str:
        return "索比光伏网"
    
    async def fetch_article_urls(self) -> List[str]:
        """获取文章URL列表 - 优先级: RSS > 静态爬取"""
        article_urls = []
        
        # 方法1: 尝试 RSS 源
        try:
            logger.info("尝试索比光伏网 RSS 源...")
            rss_urls = await self._fetch_from_rss()
            if rss_urls:
                logger.info(f"通过 RSS 找到 {len(rss_urls)} 篇文章")
                return rss_urls[:30]  # 限制数量
        except Exception as e:
            logger.warning(f"RSS 获取失败: {e}，回退到网页爬取")
        
        # 方法2: 静态网页爬取
        logger.info("开始静态网页爬取...")
        session = await self.get_session()
        
        # 索比光伏网的有效栏目（基于实际测试）
        category_urls = [
            f"{self.source_url}/news/",           # 新闻中心（已验证有效）
            "https://news.solarbe.com/",          # 新闻子站首页
            "https://news.solarbe.com/news/",     # 新闻列表页
            "https://news.solarbe.com/article/",  # 文章列表页（可能有效）
        ]
        
        for category_url in category_urls:
            try:
                logger.info(f"从 {category_url} 获取文章...")
                await asyncio.sleep(1)  # 礼貌延迟
                
                async with session.get(category_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # 可能的文章链接选择器
                        article_selectors = [
                            '.list li a',
                            '.news-list a',
                            '.article-list a',
                            '.title a',
                            'h2 a',
                            'h3 a',
                            'a[href*=".html"]',
                            'a[href*="/article/"]',
                            'a[href*="/news/"]',
                        ]
                        
                        for selector in article_selectors:
                            for link in soup.select(selector):
                                href = link.get('href', '')
                                if href and self._is_article_url(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in article_urls:
                                        article_urls.append(full_url)
                    else:
                        logger.warning(f"获取 {category_url} 失败: {response.status}")
            
            except Exception as e:
                logger.error(f"处理 {category_url} 时出错: {e}")
        
        logger.info(f"从索比光伏网总共找到 {len(article_urls)} 篇文章")
        return list(set(article_urls))[:30]
    
    async def _fetch_from_rss(self) -> List[str]:
        """从 RSS 源获取文章 URL"""
        session = await self.get_session()
        all_urls = []
        
        for feed_info in self.RSS_FEEDS:
            try:
                rss_url = feed_info['url']
                logger.info(f"获取 RSS: {rss_url}")
                
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        urls = self._parse_rss_xml(content)
                        all_urls.extend(urls)
                        logger.info(f"从 {feed_info['description']} 找到 {len(urls)} 篇文章")
                    else:
                        logger.warning(f"获取 RSS {rss_url} 失败: {response.status}")
            
            except Exception as e:
                logger.error(f"获取 RSS {feed_info['url']} 时出错: {e}")
        
        return list(set(all_urls))
    
    def _parse_rss_xml(self, xml_content: str) -> List[str]:
        """解析 RSS XML 内容"""
        urls = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # 查找所有 item 元素
            for item in root.findall('.//item'):
                link_elem = item.find('link')
                if link_elem is not None and link_elem.text:
                    url = link_elem.text.strip()
                    if url and url not in urls:
                        urls.append(url)
        
        except ET.ParseError as e:
            logger.error(f"解析 RSS XML 出错: {e}")
        
        return urls
    
    def _is_article_url(self, url: str) -> bool:
        """判断是否为文章URL"""
        # 排除非文章链接
        excluded_patterns = [
            r'/list',
            r'/index',
            r'/search',
            r'#',
            r'\.pdf$',
            r'\.jpg$',
            r'\.png$',
            r'\.gif$',
            r'javascript:',
            r'mailto:',
            r'/rss',
            r'/feed',
            r'/tag/',
            r'/category/',
            r'/author/',
            r'/page/',
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 文章URL特征
        article_patterns = [
            r'\.html$',
            r'/article/',
            r'/news/\d+',
            r'/\d{4}/\d{2}/\d{2}/',
            r'/\d{8}/',
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
                    logger.warning(f"获取文章 {url} 失败: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                author = self._extract_author(soup)
                publish_date = self._extract_date(soup, url)
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
                        'crawled_by': 'solarbe_crawler',
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
        selectors = [
            'h1',
            '.article-title',
            '.news-title',
            '.title',
            'title'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                # 清理标题中的网站名
                title = re.sub(r'[-_]\s*索比光伏网.*$', '', title)
                title = re.sub(r'[-_]\s*solarbe.*$', '', title, flags=re.IGNORECASE)
                return title
        
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content_selectors = [
            '.article-content',
            '.news-content',
            '.content',
            '.article-body',
            '.detail-content',
            'article',
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                # 移除脚本、样式、广告等
                for tag in elem(['script', 'style', 'iframe', 'ins', 'ad']):
                    tag.decompose()
                
                paragraphs = elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    # 清理尾部广告、版权信息
                    content = re.sub(r'责任编辑.*$', '', content)
                    content = re.sub(r'来源.*$', '', content)
                    content = re.sub(r'版权声明.*$', '', content, flags=re.IGNORECASE)
                    content = re.sub(r'相关阅读.*$', '', content)
                    
                    if len(content) > 100:  # 确保有足够内容
                        return content
        
        # 备用方案：查找所有段落
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True)])
        return content[:5000]  # 限制长度
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者/来源"""
        selectors = [
            '.author',
            '.source',
            '.article-info span',
            '.info span',
            '[rel="author"]',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # 提取作者信息
                author_match = re.search(r'作者[：:]\s*(\S+)', text)
                if author_match:
                    return author_match.group(1)
                
                source_match = re.search(r'来源[：:]\s*(\S+)', text)
                if source_match:
                    return source_match.group(1)
                
                return text
        
        return ""
    
    def _extract_date(self, soup: BeautifulSoup, url: str) -> str:
        """提取发布日期"""
        # 尝试从 meta 标签获取
        meta_selectors = [
            {'property': 'article:published_time'},
            {'name': 'publish_date'},
            {'name': 'pubdate'},
            {'name': 'date'},
        ]
        
        for meta_attrs in meta_selectors:
            meta = soup.find('meta', attrs=meta_attrs)
            if meta and meta.get('content'):
                return meta['content']
        
        # 尝试从页面文本中查找日期
        text = soup.get_text()
        date_patterns = [
            r'发布时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?\s*\d{1,2}[:时]\d{1,2})',
            r'发布日期[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?\s*\d{1,2}[:时]\d{1,2})',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # 从 URL 中提取日期（如果有）
        url_date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if url_date_match:
            year, month, day = url_date_match.groups()
            return f"{year}-{month}-{day}"
        
        url_date_match = re.search(r'/(\d{8})/', url)
        if url_date_match:
            date_str = url_date_match.group(1)
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # 从正文第一段提取
        content_selectors = ['.article-content', '.content', 'article']
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                first_p = elem.find('p')
                if first_p:
                    summary = first_p.get_text(strip=True)
                    if len(summary) > 50:
                        return summary[:200]
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 从 meta 标签获取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords['content'].split(',') if k.strip()]
        
        # 从标签元素获取
        tag_elements = soup.select('.tags a, .article-tags a, [rel="tag"]')
        for elem in tag_elements:
            tag_text = elem.get_text(strip=True)
            if tag_text and tag_text not in keywords:
                keywords.append(tag_text)
        
        return keywords[:10]