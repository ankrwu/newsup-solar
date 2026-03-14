"""
PV Magazine 商业板块爬虫
专门抓取工商业光伏相关内容：https://www.pv-magazine.com/category/business/
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class PVMagazineBusinessCrawler(BaseCrawler):
    """PV Magazine 商业板块爬虫，专注工商业光伏"""
    
    @property
    def source_url(self) -> str:
        return "https://www.pv-magazine.com"
    
    @property
    def source_display_name(self) -> str:
        return "PV Magazine Business"
    
    @property
    def business_category_url(self) -> str:
        """商业板块URL"""
        return f"{self.source_url}/category/business/"
    
    async def fetch_article_urls(self) -> List[str]:
        """从PV Magazine商业板块获取文章URL"""
        session = await self.get_session()
        urls = []
        
        try:
            # 访问商业板块
            logger.info(f"Fetching articles from {self.business_category_url}")
            async with session.get(self.business_category_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # 查找文章链接
                    # PV Magazine 的文章通常有这样的结构
                    article_selectors = [
                        'article a[href*="/news/"]',
                        'article a[href*="/business/"]',
                        '.post-title a',
                        '.entry-title a',
                        'h2 a',
                        'a[href*="/202"]',  # 包含日期的链接
                    ]
                    
                    for selector in article_selectors:
                        for link in soup.select(selector):
                            href = link.get('href', '')
                            if href and self._is_business_article(href):
                                full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                if full_url not in urls:
                                    urls.append(full_url)
                    
                    logger.info(f"Found {len(urls)} potential business articles from PV Magazine")
                    
                    # 也检查分页
                    urls.extend(await self._fetch_pagination_urls(soup))
                    
                    # 去重并返回前20个
                    urls = list(set(urls))
                    return urls[:20]
                    
                else:
                    logger.error(f"Failed to fetch {self.business_category_url}: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching PV Magazine Business URLs: {e}")
            return []
    
    async def _fetch_pagination_urls(self, soup: BeautifulSoup) -> List[str]:
        """获取分页链接"""
        pagination_urls = []
        
        try:
            # 查找分页链接
            pagination_links = soup.select('.pagination a, .page-numbers a')
            for link in pagination_links:
                href = link.get('href', '')
                if href and 'page' in href.lower() and self.business_category_url in href:
                    if href not in pagination_urls:
                        pagination_urls.append(href)
            
            logger.info(f"Found {len(pagination_urls)} pagination pages")
            
            # 获取每个分页的文章
            session = await self.get_session()
            all_urls = []
            
            for page_url in pagination_urls[:2]:  # 只获取前2个分页
                try:
                    async with session.get(page_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_soup = BeautifulSoup(html, 'lxml')
                            
                            # 提取文章链接
                            for link in page_soup.select('article a[href*="/news/"], article a[href*="/business/"]'):
                                href = link.get('href', '')
                                if href and self._is_business_article(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in all_urls:
                                        all_urls.append(full_url)
                except Exception as e:
                    logger.warning(f"Error fetching pagination page {page_url}: {e}")
            
            return all_urls
            
        except Exception as e:
            logger.error(f"Error in pagination fetching: {e}")
            return []
    
    def _is_business_article(self, url: str) -> bool:
        """判断URL是否为商业相关文章"""
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
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 检查是否为文章URL
        article_patterns = [
            r'/news/',
            r'/business/',
            r'/\d{4}/\d{2}/\d{2}/',  # 包含日期的URL
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """解析PV Magazine商业文章"""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # 提取标题
                title_elem = soup.find('h1', class_=re.compile(r'title|headline|entry-title'))
                if not title_elem:
                    title_elem = soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # 提取内容
                content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'content|article-body|entry-content'))
                content = ""
                if content_elem:
                    # 获取段落文本
                    paragraphs = content_elem.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # 提取作者
                author_elem = soup.find('span', class_=re.compile(r'author|byline'))
                author = author_elem.get_text(strip=True) if author_elem else ""
                
                # 提取发布日期
                date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|published|posted-on'))
                publish_date = ""
                if date_elem:
                    publish_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                # 提取摘要
                summary_elem = soup.find('meta', attrs={'name': 'description'})
                if not summary_elem:
                    summary_elem = soup.find('meta', attrs={'property': 'og:description'})
                summary = summary_elem.get('content', '') if summary_elem else ""
                
                # 提取标签/分类
                tags = []
                tags_section = soup.find('div', class_=re.compile(r'tags|categories'))
                if tags_section:
                    for tag in tags_section.find_all('a'):
                        tag_text = tag.get_text(strip=True)
                        if tag_text:
                            tags.append(tag_text)
                
                # 提取商业相关关键词
                business_keywords = self._extract_business_keywords(soup, content)
                
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
                    keywords=business_keywords,
                    categories=tags,
                    raw_html=html[:10000],  # 存储前10000字符用于调试
                    metadata={
                        'source_section': 'business',
                        'crawled_by': 'pv_magazine_business',
                        'business_related': True,
                        'content_length': len(content),
                    }
                )
                
                # 添加商业分析标记
                article['metadata']['business_analysis'] = {
                    'is_commercial': self._is_commercial_content(content),
                    'keywords_found': business_keywords,
                    'extraction_method': 'pv_magazine_business_crawler',
                }
                
                logger.debug(f"Parsed business article: {title}")
                return article
                
        except Exception as e:
            logger.error(f"Error parsing PV Magazine Business article {url}: {e}")
            return None
    
    def _extract_business_keywords(self, soup: BeautifulSoup, content: str) -> List[str]:
        """提取商业相关关键词"""
        keywords = []
        content_lower = content.lower()
        
        # 商业光伏关键词
        commercial_keywords = [
            'commercial', 'industrial', 'business', 'C&I',
            'PPA', 'power purchase agreement', 'leasing',
            'financing', 'investment', 'ROI', 'payback',
            'tax credit', 'ITC', 'incentive', 'rebate',
            'market', 'industry', 'sector', 'growth',
            'project', 'development', 'installation',
            'corporate', 'enterprise', 'utility',
        ]
        
        # 检查内容中的关键词
        for keyword in commercial_keywords:
            if keyword.lower() in content_lower:
                keywords.append(keyword)
        
        # 从meta标签提取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            meta_keys = [k.strip() for k in meta_keywords['content'].split(',')]
            keywords.extend(meta_keys)
        
        # 去重
        keywords = list(set(keywords))
        
        return keywords
    
    def _is_commercial_content(self, content: str) -> bool:
        """判断内容是否与商业光伏相关"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # 商业光伏相关术语
        commercial_terms = [
            'commercial solar',
            'industrial solar',
            'business solar',
            'C&I solar',
            'commercial PV',
            'industrial PV',
            'commercial and industrial',
            'PPA',
            'power purchase agreement',
            'solar lease',
            'commercial market',
            'business case',
            'ROI',
            'payback period',
            'investment tax credit',
            'commercial incentive',
        ]
        
        # 检查是否包含商业术语
        for term in commercial_terms:
            if term.lower() in content_lower:
                return True
        
        return False
    
    async def close(self):
        """关闭会话"""
        await self.close_session()