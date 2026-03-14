"""
Solar Power World 商业板块爬虫
专门抓取商业光伏相关内容：https://www.solarpowerworldonline.com/category/commercial/
"""

import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from ..base import BaseCrawler

logger = logging.getLogger(__name__)


class SolarPowerWorldCommercialCrawler(BaseCrawler):
    """Solar Power World 商业板块爬虫，专注商业光伏安装"""
    
    @property
    def source_url(self) -> str:
        return "https://www.solarpowerworldonline.com"
    
    @property
    def source_display_name(self) -> str:
        return "Solar Power World Commercial"
    
    @property
    def commercial_category_url(self) -> str:
        """商业板块URL"""
        return f"{self.source_url}/category/commercial/"
    
    async def fetch_article_urls(self) -> List[str]:
        """从Solar Power World商业板块获取文章URL"""
        session = await self.get_session()
        urls = []
        
        try:
            # 访问商业板块
            logger.info(f"Fetching articles from {self.commercial_category_url}")
            async with session.get(self.commercial_category_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # 查找文章链接
                    # Solar Power World 的文章结构
                    article_selectors = [
                        'article a',
                        '.post-title a',
                        '.entry-title a',
                        '.post-content a',
                        'h2 a',
                        'h3 a',
                        'a[href*="/article/"]',
                        'a[href*="/commercial/"]',
                    ]
                    
                    for selector in article_selectors:
                        for link in soup.select(selector):
                            href = link.get('href', '')
                            if href and self._is_commercial_article(href):
                                full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                if full_url not in urls:
                                    urls.append(full_url)
                    
                    logger.info(f"Found {len(urls)} potential commercial articles from Solar Power World")
                    
                    # 也检查分页
                    urls.extend(await self._fetch_pagination_urls(soup))
                    
                    # 去重并返回前15个
                    urls = list(set(urls))
                    return urls[:15]
                    
                else:
                    logger.error(f"Failed to fetch {self.commercial_category_url}: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Solar Power World Commercial URLs: {e}")
            return []
    
    async def _fetch_pagination_urls(self, soup: BeautifulSoup) -> List[str]:
        """获取分页链接"""
        pagination_urls = []
        
        try:
            # 查找分页链接
            pagination_selectors = [
                '.pagination a',
                '.page-numbers a',
                '.nav-links a',
                'a.next',
                'a.prev',
            ]
            
            for selector in pagination_selectors:
                for link in soup.select(selector):
                    href = link.get('href', '')
                    if href and 'page' in href.lower() and self.commercial_category_url in href:
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
                            for link in page_soup.select('article a, .post-title a'):
                                href = link.get('href', '')
                                if href and self._is_commercial_article(href):
                                    full_url = href if href.startswith('http') else f"{self.source_url}{href}"
                                    if full_url not in all_urls:
                                        all_urls.append(full_url)
                except Exception as e:
                    logger.warning(f"Error fetching pagination page {page_url}: {e}")
            
            return all_urls
            
        except Exception as e:
            logger.error(f"Error in pagination fetching: {e}")
            return []
    
    def _is_commercial_article(self, url: str) -> bool:
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
            r'/feed/',
            r'wp-content/',
            r'wp-json/',
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 检查是否为文章URL
        article_patterns = [
            r'/article/',
            r'/commercial/',
            r'/\d{4}/\d{2}/',  # 包含年月
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """解析Solar Power World商业文章"""
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # 提取标题
                title_elem = soup.find('h1', class_=re.compile(r'title|entry-title|post-title|headline'))
                if not title_elem:
                    title_elem = soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # 提取内容
                content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'entry-content|article-content|post-content'))
                content = ""
                if content_elem:
                    # 获取段落文本
                    paragraphs = content_elem.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # 提取作者
                author_elem = soup.find('span', class_=re.compile(r'author|byline'))
                if not author_elem:
                    author_elem = soup.find('a', class_=re.compile(r'author'))
                author = author_elem.get_text(strip=True) if author_elem else ""
                
                # 提取发布日期
                date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|posted-on'))
                publish_date = ""
                if date_elem:
                    publish_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                
                # 提取摘要
                summary_elem = soup.find('meta', attrs={'property': 'og:description'})
                if not summary_elem:
                    summary_elem = soup.find('meta', attrs={'name': 'description'})
                summary = summary_elem.get('content', '') if summary_elem else ""
                
                # 提取标签
                tags = []
                tags_section = soup.find('div', class_=re.compile(r'tags|categories'))
                if tags_section:
                    for tag in tags_section.find_all('a'):
                        tag_text = tag.get_text(strip=True)
                        if tag_text:
                            tags.append(tag_text)
                
                # 提取商业安装相关关键词
                installation_keywords = self._extract_installation_keywords(soup, content)
                
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
                    keywords=installation_keywords,
                    categories=tags,
                    raw_html=html[:8000],  # 存储前8000字符用于调试
                    metadata={
                        'source_section': 'commercial',
                        'crawled_by': 'solar_power_world_commercial',
                        'installation_focused': True,
                        'content_length': len(content),
                    }
                )
                
                # 添加安装分析标记
                article['metadata']['installation_analysis'] = {
                    'is_commercial_installation': self._is_commercial_installation(content),
                    'keywords_found': installation_keywords,
                    'project_details': self._extract_project_details(content),
                    'extraction_method': 'solar_power_world_commercial_crawler',
                }
                
                logger.debug(f"Parsed commercial installation article: {title}")
                return article
                
        except Exception as e:
            logger.error(f"Error parsing Solar Power World Commercial article {url}: {e}")
            return None
    
    def _extract_installation_keywords(self, soup: BeautifulSoup, content: str) -> List[str]:
        """提取安装相关关键词"""
        keywords = []
        content_lower = content.lower()
        
        # 商业安装关键词
        installation_keywords = [
            'commercial installation',
            'industrial installation',
            'business installation',
            'rooftop installation',
            'solar installer',
            'installation company',
            'EPC',
            'engineering procurement construction',
            'contractor',
            'project development',
            'system design',
            'permitting',
            'interconnection',
            'commissioning',
            'O&M',
            'operations and maintenance',
            'warranty',
            'performance guarantee',
            'turnkey',
            'design-build',
        ]
        
        # 检查内容中的关键词
        for keyword in installation_keywords:
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
    
    def _is_commercial_installation(self, content: str) -> bool:
        """判断内容是否与商业安装相关"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # 商业安装相关术语
        installation_terms = [
            'commercial installation',
            'industrial installation',
            'business installation',
            'rooftop installation',
            'solar installer',
            'EPC contractor',
            'project development',
            'system design',
            'permitting',
            'interconnection',
            'commissioning',
            'turnkey',
            'design-build',
        ]
        
        # 检查是否包含安装术语
        for term in installation_terms:
            if term.lower() in content_lower:
                return True
        
        return False
    
    def _extract_project_details(self, content: str) -> Dict[str, Any]:
        """提取项目详情信息"""
        details = {
            'system_size': None,
            'location': None,
            'installer': None,
            'completion_date': None,
            'estimated_cost': None,
        }
        
        # 提取系统规模 (MW, kW)
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*MW',  # 10 MW
            r'(\d+(?:\.\d+)?)\s*megawatts',
            r'(\d+(?:\.\d+)?)\s*kW',  # 100 kW
            r'(\d+(?:\.\d+)?)\s*kilowatts',
            r'(\d+(?:,\d+)*)\s*watt',  # 100,000 watt
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                details['system_size'] = matches[0]
                break
        
        # 提取位置信息 (简单实现)
        location_keywords = ['in ', 'at ', 'located in ', 'based in ']
        for keyword in location_keywords:
            idx = content.lower().find(keyword)
            if idx != -1:
                # 提取位置短语
                start = idx + len(keyword)
                end = min(start + 50, len(content))
                location_phrase = content[start:end].split('.')[0].split(',')[0].strip()
                if location_phrase and len(location_phrase) > 3:
                    details['location'] = location_phrase
                    break
        
        # 提取安装商名称 (简单实现)
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corporation|Corp|Inc|LLC|Ltd)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+Solar',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Energy',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Renewables',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, content)
            if matches:
                details['installer'] = matches[0]
                break
        
        return details
    
    async def close(self):
        """关闭会话"""
        await self.close_session()