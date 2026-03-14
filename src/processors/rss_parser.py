"""
RSS 订阅源支持模块
支持 RSS 2.0 和 Atom 格式的新闻订阅
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

import feedparser
from feedparser import FeedParserDict

logger = logging.getLogger(__name__)


@dataclass
class RSSArticle:
    """RSS 文章数据结构"""
    title: str
    url: str
    content: str
    summary: str
    author: str
    publish_date: str
    source: str
    source_url: str
    article_id: str
    keywords: List[str]
    raw_entry: Dict[str, Any]


class RSSParser:
    """RSS/Atom 订阅解析器"""
    
    def __init__(self):
        self.user_agent = 'newsup-solar/1.0 (Solar News Aggregator)'
    
    def parse_feed(self, feed_url: str, source_name: str, 
                   source_url: str, limit: int = 50) -> List[RSSArticle]:
        """
        解析 RSS/Atom 订阅源
        
        Args:
            feed_url: RSS 订阅链接
            source_name: 数据源名称
            source_url: 数据源网站地址
            limit: 最大文章数
        
        Returns:
            文章列表
        """
        try:
            logger.info(f"Parsing RSS feed: {feed_url}")
            
            # 使用 feedparser 解析
            feed = feedparser.parse(
                feed_url,
                agent=self.user_agent,
                request_headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'
                }
            )
            
            if feed.bozo:  # 解析错误
                logger.warning(f"RSS feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            articles = []
            entries = feed.entries[:limit]
            
            for entry in entries:
                try:
                    article = self._parse_entry(entry, source_name, source_url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
            
            logger.info(f"Parsed {len(articles)} articles from {source_name} RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []
    
    def _parse_entry(self, entry: FeedParserDict, 
                     source_name: str, source_url: str) -> Optional[RSSArticle]:
        """解析单个 RSS 条目"""
        # 提取标题
        title = self._get_title(entry)
        if not title:
            return None
        
        # 提取链接
        url = self._get_link(entry)
        if not url:
            return None
        
        # 提取内容
        content = self._get_content(entry)
        
        # 提取摘要
        summary = self._get_summary(entry)
        
        # 提取作者
        author = self._get_author(entry)
        
        # 提取发布日期
        publish_date = self._get_publish_date(entry)
        
        # 提取关键词/标签
        keywords = self._get_keywords(entry)
        
        # 生成文章ID
        article_id = self._generate_id(url)
        
        return RSSArticle(
            title=title,
            url=url,
            content=content,
            summary=summary,
            author=author,
            publish_date=publish_date,
            source=source_name,
            source_url=source_url,
            article_id=article_id,
            keywords=keywords,
            raw_entry=dict(entry)
        )
    
    def _get_title(self, entry: FeedParserDict) -> str:
        """提取标题"""
        if hasattr(entry, 'title'):
            return entry.title.strip()
        return ""
    
    def _get_link(self, entry: FeedParserDict) -> str:
        """提取链接"""
        # 尝试多种链接字段
        if hasattr(entry, 'link') and entry.link:
            return entry.link
        
        if hasattr(entry, 'links') and entry.links:
            for link in entry.links:
                if link.get('rel') == 'alternate':
                    return link.get('href', '')
            return entry.links[0].get('href', '')
        
        return ""
    
    def _get_content(self, entry: FeedParserDict) -> str:
        """提取内容"""
        # 尝试 content 字段
        if hasattr(entry, 'content') and entry.content:
            content_list = entry.content
            if isinstance(content_list, list) and content_list:
                return content_list[0].get('value', '')
            return str(content_list)
        
        # 尝试 content_encoded
        if hasattr(entry, 'content_encoded'):
            return entry.content_encoded
        
        # 尝试 summary 作为内容
        if hasattr(entry, 'summary'):
            return entry.summary
        
        return ""
    
    def _get_summary(self, entry: FeedParserDict) -> str:
        """提取摘要"""
        if hasattr(entry, 'summary'):
            # 清理 HTML 标签
            import re
            summary = entry.summary
            summary = re.sub(r'<[^>]+>', '', summary)  # 移除 HTML 标签
            summary = re.sub(r'\s+', ' ', summary)  # 合并空白
            return summary.strip()[:500]  # 限制长度
        
        return ""
    
    def _get_author(self, entry: FeedParserDict) -> str:
        """提取作者"""
        if hasattr(entry, 'author'):
            return entry.author.strip()
        
        if hasattr(entry, 'authors') and entry.authors:
            return ', '.join([a.get('name', '') for a in entry.authors if a.get('name')])
        
        return ""
    
    def _get_publish_date(self, entry: FeedParserDict) -> str:
        """提取发布日期"""
        # 尝试多种日期字段
        date_fields = ['published', 'pubDate', 'updated', 'created']
        
        for field in date_fields:
            if hasattr(entry, field):
                date_value = getattr(entry, field)
                if date_value:
                    # 尝试解析日期
                    try:
                        if hasattr(entry, f'{field}_parsed') and getattr(entry, f'{field}_parsed'):
                            parsed = getattr(entry, f'{field}_parsed')
                            return datetime(*parsed[:6]).isoformat()
                    except:
                        pass
                    return str(date_value)
        
        return ""
    
    def _get_keywords(self, entry: FeedParserDict) -> List[str]:
        """提取关键词/标签"""
        keywords = []
        
        # RSS categories
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                term = tag.get('term', '') or tag.get('label', '')
                if term:
                    keywords.append(term.strip())
        
        # 尝试 keywords 字段
        if hasattr(entry, 'keywords'):
            kw = entry.keywords
            if isinstance(kw, str):
                keywords.extend([k.strip() for k in kw.split(',')])
            elif isinstance(kw, list):
                keywords.extend(kw)
        
        return list(set(keywords))[:10]
    
    def _generate_id(self, url: str) -> str:
        """生成文章 ID"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]


def rss_article_to_dict(article: RSSArticle) -> Dict[str, Any]:
    """将 RSSArticle 转换为字典格式"""
    return {
        'article_id': article.article_id,
        'title': article.title,
        'url': article.url,
        'source': article.source,
        'source_url': article.source_url,
        'author': article.author,
        'publish_date': article.publish_date,
        'crawl_date': datetime.utcnow().isoformat(),
        'content': article.content,
        'summary': article.summary,
        'keywords': article.keywords,
        'categories': [],
        'processed': False,
        'metadata': {
            'source_type': 'rss',
            'raw_entry_keys': list(article.raw_entry.keys()),
        }
    }


# 预定义的 RSS 订阅源
RSS_FEEDS = {
    # 英文源
    'en': {
        'pv_magazine': {
            'name': 'PV Magazine',
            'feed_url': 'https://www.pv-magazine.com/feed/',
            'source_url': 'https://www.pv-magazine.com',
        },
        'pv_magazine_us': {
            'name': 'PV Magazine USA',
            'feed_url': 'https://www.pv-magazine-usa.com/feed/',
            'source_url': 'https://www.pv-magazine-usa.com',
        },
        'pv_magazine_australia': {
            'name': 'PV Magazine Australia',
            'feed_url': 'https://www.pv-magazine-australia.com/feed/',
            'source_url': 'https://www.pv-magazine-australia.com',
        },
        'solar_power_world': {
            'name': 'Solar Power World',
            'feed_url': 'https://www.solarpowerworldonline.com/feed/',
            'source_url': 'https://www.solarpowerworldonline.com',
        },
        'renewable_energy_world': {
            'name': 'Renewable Energy World',
            'feed_url': 'https://www.renewableenergyworld.com/feed/',
            'source_url': 'https://www.renewableenergyworld.com',
        },
        'pv_tech': {
            'name': 'PV Tech',
            'feed_url': 'https://www.pv-tech.org/feed',
            'source_url': 'https://www.pv-tech.org',
        },
        'solar_reviews': {
            'name': 'Solar Reviews',
            'feed_url': 'https://www.solarreviews.com/feed',
            'source_url': 'https://www.solarreviews.com',
        },
        'cleantechnica_solar': {
            'name': 'CleanTechnica Solar',
            'feed_url': 'https://cleantechnica.com/solar-energy/feed/',
            'source_url': 'https://cleantechnica.com',
        },
    },
    
    # 中文源
    'zh': {
        'pv_magazine_china': {
            'name': 'PV Magazine 中国',
            'feed_url': 'https://www.pv-magazine-china.com/feed/',
            'source_url': 'https://www.pv-magazine-china.com',
        },
        'bjx_guangfu': {
            'name': '北极星光伏网',
            'feed_url': 'https://guangfu.bjx.com.cn/rss.xml',
            'source_url': 'https://guangfu.bjx.com.cn',
        },
        'china5e_solar': {
            'name': '中国能源网-太阳能',
            'feed_url': 'https://www.china5e.com/rss.php?catid=101',
            'source_url': 'https://www.china5e.com',
        },
        'solar_ofweek': {
            'name': 'OFweek太阳能光伏',
            'feed_url': 'https://solar.ofweek.com/rss.jsp',
            'source_url': 'https://solar.ofweek.com',
        },
    },
}


def get_rss_feeds(language: str = 'all') -> Dict[str, Dict[str, str]]:
    """
    获取 RSS 订阅源列表
    
    Args:
        language: 'en', 'zh', 或 'all'
    
    Returns:
        RSS 订阅源字典
    """
    if language == 'all':
        return {**RSS_FEEDS['en'], **RSS_FEEDS['zh']}
    elif language in RSS_FEEDS:
        return RSS_FEEDS[language]
    return {}
