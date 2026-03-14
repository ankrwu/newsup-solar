"""
文章分类器
基于内容将文章分类为新闻、政策、市场等类型
"""

import re
import logging
from typing import Dict, Any, List

from config.commercial_solar_keywords import (
    POLICY_KEYWORDS,
    MARKET_KEYWORDS,
    classify_content_type,
)

logger = logging.getLogger(__name__)


class ArticleClassifier:
    """文章分类器"""
    
    def __init__(self):
        self.news_keywords = [
            'announced', 'launched', 'completed', 'started',
            'signed', 'agreement', 'deal', 'partnership',
            'awarded', 'won', 'selected', 'chosen',
            'opened', 'inaugurated', 'celebrated',
            'new', 'latest', 'recent', 'upcoming',
        ]
        
        self.technology_keywords = [
            'technology', 'innovation', 'research', 'development',
            'breakthrough', 'advance', 'improvement', 'enhancement',
            'efficiency', 'performance', 'output', 'yield',
            'cell', 'module', 'panel', 'inverter', 'battery',
            'storage', 'tracking', 'monitoring', 'control',
        ]
        
        self.finance_keywords = [
            'funding', 'investment', 'finance', 'capital',
            'fund', 'raise', 'series', 'round',
            'venture', 'private equity', 'angel',
            'loan', 'debt', 'equity', 'bond',
            'valuation', 'valuation', 'revenue', 'profit',
        ]
    
    def classify(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """对文章进行分类"""
        classified = article.copy()
        
        # 基础内容类型分类
        content_classification = self._classify_content_type(classified)
        classified.update(content_classification)
        
        # 技术分类
        tech_classification = self._classify_technology(classified)
        classified.update(tech_classification)
        
        # 金融分类
        finance_classification = self._classify_finance(classified)
        classified.update(finance_classification)
        
        # 添加分类元数据
        if 'metadata' not in classified:
            classified['metadata'] = {}
        
        classified['metadata']['classified'] = True
        classified['metadata']['classification_timestamp'] = self._get_timestamp()
        
        logger.debug(f"Classified article: {classified.get('title', 'Unknown')}")
        
        return classified
    
    def _classify_content_type(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """分类内容类型：新闻、政策、市场"""
        text = f"{article.get('title', '')} {article.get('content', '')}"
        
        # 使用关键词分类
        classification = classify_content_type(text)
        
        # 添加新闻分类
        classification['is_news'] = self._is_news_content(text)
        
        return {
            'content_type': self._determine_primary_type(classification),
            'content_subtypes': self._get_content_subtypes(classification),
        }
    
    def _classify_technology(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """分类技术相关内容"""
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        
        tech_score = 0
        tech_keywords_found = []
        
        for keyword in self.technology_keywords:
            if keyword.lower() in text:
                tech_score += 1
                tech_keywords_found.append(keyword)
        
        return {
            'is_technology': tech_score > 0,
            'technology_score': tech_score,
            'technology_keywords': tech_keywords_found,
        }
    
    def _classify_finance(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """分类金融相关内容"""
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        
        finance_score = 0
        finance_keywords_found = []
        
        for keyword in self.finance_keywords:
            if keyword.lower() in text:
                finance_score += 1
                finance_keywords_found.append(keyword)
        
        return {
            'is_finance': finance_score > 0,
            'finance_score': finance_score,
            'finance_keywords': finance_keywords_found,
        }
    
    def _is_news_content(self, text: str) -> bool:
        """判断是否为新闻内容"""
        text_lower = text.lower()
        
        for keyword in self.news_keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _determine_primary_type(self, classification: Dict[str, Any]) -> str:
        """确定主要类型"""
        if classification.get('is_policy', False):
            return 'policy'
        elif classification.get('is_market', False):
            return 'market'
        elif classification.get('is_news', False):
            return 'news'
        else:
            return 'general'
    
    def _get_content_subtypes(self, classification: Dict[str, Any]) -> List[str]:
        """获取内容子类型"""
        subtypes = []
        
        if classification.get('is_policy', False):
            subtypes.append('policy')
        if classification.get('is_market', False):
            subtypes.append('market')
        if classification.get('is_news', False):
            subtypes.append('news')
        
        return subtypes
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def validate_classification(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """验证分类结果"""
        validation = {
            'valid': True,
            'issues': [],
            'suggestions': [],
        }
        
        # 检查必要字段
        required_fields = ['content_type', 'content_subtypes']
        for field in required_fields:
            if field not in article:
                validation['valid'] = False
                validation['issues'].append(f'Missing classification field: {field}')
        
        # 检查内容类型是否合理
        content_type = article.get('content_type', '')
        if content_type not in ['news', 'policy', 'market', 'general']:
            validation['issues'].append(f'Invalid content type: {content_type}')
            validation['suggestions'].append('Content type should be news, policy, market, or general')
        
        # 检查子类型是否为空
        subtypes = article.get('content_subtypes', [])
        if not subtypes:
            validation['issues'].append('No content subtypes identified')
            validation['suggestions'].append('Content may not have clear classification')
        
        return validation