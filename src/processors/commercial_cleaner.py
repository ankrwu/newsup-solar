"""
工商业光伏专用文章清洗器和分类器
"""

import re
from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime

from .cleaner import ArticleCleaner
from config.commercial_solar_keywords import (
    COMMERCIAL_SOLAR_KEYWORDS,
    POLICY_KEYWORDS,
    MARKET_KEYWORDS,
    REGION_KEYWORDS,
    PROJECT_SCALE_KEYWORDS,
    is_commercial_solar_content,
    classify_content_type,
    extract_project_scale,
    extract_regions,
)

logger = logging.getLogger(__name__)


class CommercialSolarCleaner(ArticleCleaner):
    """工商业光伏专用清洗器和分析器"""
    
    def __init__(self):
        super().__init__()
        
        # 工商业光伏专用关键词
        self.commercial_keywords = COMMERCIAL_SOLAR_KEYWORDS
        
        # 商业模式关键词
        self.business_model_keywords = [
            'PPA', 'power purchase agreement', 'solar lease',
            'third-party ownership', 'energy service agreement',
            'virtual PPA', 'corporate PPA', 'community solar',
            'solar financing', 'solar loan', 'capital lease',
            'operating lease', 'off-balance sheet',
        ]
        
        # 政策类型关键词
        self.policy_type_keywords = {
            'tax': ['tax credit', 'ITC', 'accelerated depreciation', 'MACRS'],
            'subsidy': ['rebate', 'subsidy', 'grant', 'incentive'],
            'regulation': ['regulation', 'mandate', 'standard', 'requirement'],
            'tariff': ['tariff', 'duty', 'import tax'],
            'grid': ['net metering', 'grid connection', 'interconnection'],
            'permitting': ['permit', 'approval', 'zoning', 'land use'],
        }
    
    def clean(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """清洗并分析工商业光伏文章"""
        # 首先进行基础清洗
        cleaned = super().clean(article)
        
        # 添加工商业光伏专项分析
        cleaned = self._analyze_commercial_solar(cleaned)
        
        # 添加分类标签
        cleaned = self._add_commercial_classification(cleaned)
        
        # 提取商业相关信息
        cleaned = self._extract_business_info(cleaned)
        
        # 计算工商业光伏相关度，存储在metadata中
        commercial_score = self._calculate_commercial_relevance(cleaned)
        if 'metadata' not in cleaned:
            cleaned['metadata'] = {}
        cleaned['metadata']['commercial_relevance_score'] = commercial_score
        cleaned['metadata']['commercial_processed'] = True
        cleaned['metadata']['commercial_processing_date'] = self._get_timestamp()
        
        logger.debug(f"商业光伏清洗完成: {cleaned.get('title', 'Unknown')}")
        
        return cleaned
    
    def _analyze_commercial_solar(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """分析工商业光伏相关内容"""
        analysis = {
            'is_commercial_solar': False,
            'content_type': 'unknown',  # news/policy/market
            'sub_type': 'unknown',      # 更细分的类型
            'business_models': [],
            'policy_types': [],
            'market_segments': [],
            'project_scale': 'unknown',
            'regions': [],
            'keywords_found': [],
        }
        
        # 合并标题和内容进行分析
        text_for_analysis = f"{article.get('title', '')} {article.get('content', '')}"
        
        # 检查是否为工商业光伏内容
        analysis['is_commercial_solar'] = is_commercial_solar_content(text_for_analysis)
        
        # 内容类型分类
        content_classification = classify_content_type(text_for_analysis)
        if content_classification['is_policy']:
            analysis['content_type'] = 'policy'
        elif content_classification['is_market']:
            analysis['content_type'] = 'market'
        else:
            analysis['content_type'] = 'news'
        
        analysis['keywords_found'] = content_classification['keywords_found']
        
        # 提取商业模式
        analysis['business_models'] = self._extract_business_models(text_for_analysis)
        
        # 提取政策类型（如果是政策类内容）
        if analysis['content_type'] == 'policy':
            analysis['policy_types'] = self._extract_policy_types(text_for_analysis)
            analysis['sub_type'] = self._determine_policy_subtype(analysis['policy_types'])
        
        # 提取市场细分（如果是市场类内容）
        elif analysis['content_type'] == 'market':
            analysis['market_segments'] = self._extract_market_segments(text_for_analysis)
            analysis['sub_type'] = 'market_report'
        
        # 提取项目规模
        analysis['project_scale'] = extract_project_scale(text_for_analysis)
        
        # 提取地域信息
        analysis['regions'] = extract_regions(text_for_analysis)
        
        # 添加到文章 metadata 字段
        if 'metadata' not in article:
            article['metadata'] = {}
        article['metadata']['commercial_analysis'] = analysis
        
        return article
    
    def _add_commercial_classification(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """添加工商业光伏分类标签"""
        # 从 metadata 中获取 commercial_analysis
        analysis = article.get('metadata', {}).get('commercial_analysis', {})
        if not analysis:
            return article
        
        tags = []
        
        # 添加基础标签
        if analysis['is_commercial_solar']:
            tags.append('commercial_solar')
        
        # 内容类型标签
        if analysis['content_type'] != 'unknown':
            tags.append(f"type_{analysis['content_type']}")
        
        # 子类型标签
        if analysis['sub_type'] != 'unknown':
            tags.append(f"subtype_{analysis['sub_type']}")
        
        # 商业模式标签
        for model in analysis['business_models']:
            tags.append(f"business_model_{model.lower().replace(' ', '_')}")
        
        # 政策类型标签
        for policy_type in analysis['policy_types']:
            tags.append(f"policy_{policy_type}")
        
        # 地域标签
        for region in analysis['regions']:
            tags.append(f"region_{region}")
        
        # 项目规模标签
        if analysis['project_scale'] != 'unknown':
            tags.append(f"scale_{analysis['project_scale']}")
        
        # 添加到文章 metadata 字段
        if 'metadata' not in article:
            article['metadata'] = {}
        
        # 合并现有 tags
        existing_tags = article['metadata'].get('tags', [])
        all_tags = list(set(existing_tags + tags))
        article['metadata']['tags'] = all_tags
        
        return article
    
    def _extract_business_info(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """提取商业相关信息"""
        text = f"{article.get('title', '')} {article.get('content', '')}"
        
        # 提取公司名称（简单实现）
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corporation|Corp|Inc|LLC|Ltd|Company)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\'s',  # 公司所有格
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        # 提取数字信息（规模、投资额等）
        numbers_info = self._extract_numbers_info(text)
        
        # 添加到文章 metadata 字段
        if 'metadata' not in article:
            article['metadata'] = {}
        if 'commercial_analysis' not in article['metadata']:
            article['metadata']['commercial_analysis'] = {}
        
        article['metadata']['commercial_analysis']['companies_mentioned'] = list(set(companies))
        article['metadata']['commercial_analysis']['numbers_info'] = numbers_info
        
        return article
    
    def _calculate_commercial_relevance(self, article: Dict[str, Any]) -> float:
        """计算工商业光伏相关度"""
        # 从 metadata 中获取 commercial_analysis
        analysis = article.get('metadata', {}).get('commercial_analysis', {})
        if not analysis:
            return 0.0
        
        # 基础分数
        score = 0.0
        
        # 是否为工商业光伏内容
        if analysis['is_commercial_solar']:
            score += 3.0
        
        # 内容类型权重
        if analysis['content_type'] == 'policy':
            score += 2.0  # 政策内容通常更重要
        elif analysis['content_type'] == 'market':
            score += 1.5  # 市场分析也重要
        
        # 商业模式数量
        score += len(analysis['business_models']) * 0.5
        
        # 政策类型数量
        score += len(analysis['policy_types']) * 0.3
        
        # 项目规模识别
        if analysis['project_scale'] != 'unknown':
            score += 1.0
        
        # 地域识别
        score += len(analysis['regions']) * 0.2
        
        # 关键词数量
        score += len(analysis['keywords_found']) * 0.1
        
        # 归一化到0-10分
        score = min(score, 10.0)
        
        return round(score, 2)
    
    def _extract_business_models(self, text: str) -> List[str]:
        """提取商业模式信息"""
        text_lower = text.lower()
        models_found = []
        
        for model in self.business_model_keywords:
            if model.lower() in text_lower:
                models_found.append(model)
        
        return models_found
    
    def _extract_policy_types(self, text: str) -> List[str]:
        """提取政策类型"""
        text_lower = text.lower()
        policy_types = []
        
        for policy_type, keywords in self.policy_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    policy_types.append(policy_type)
                    break  # 每种类型只添加一次
        
        return policy_types
    
    def _extract_market_segments(self, text: str) -> List[str]:
        """提取市场细分"""
        segments = []
        text_lower = text.lower()
        
        # 定义市场细分关键词
        market_segments = {
            'residential': ['residential', 'home', 'household'],
            'commercial': ['commercial', 'business', 'retail', 'office'],
            'industrial': ['industrial', 'manufacturing', 'factory', 'warehouse'],
            'utility': ['utility', 'utility-scale', 'power plant', 'solar farm'],
            'community': ['community solar', 'shared solar', 'solar garden'],
            'agricultural': ['agricultural', 'farm', 'agrivoltaic'],
        }
        
        for segment, keywords in market_segments.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    segments.append(segment)
                    break
        
        return segments
    
    def _determine_policy_subtype(self, policy_types: List[str]) -> str:
        """确定政策子类型"""
        if not policy_types:
            return 'general_policy'
        
        # 优先级：tax > subsidy > regulation > tariff > grid > permitting
        priority_order = ['tax', 'subsidy', 'regulation', 'tariff', 'grid', 'permitting']
        
        for policy_type in priority_order:
            if policy_type in policy_types:
                return f"{policy_type}_policy"
        
        return 'general_policy'
    
    def _extract_numbers_info(self, text: str) -> Dict[str, Any]:
        """提取数字信息（投资额、规模等）"""
        numbers_info = {
            'investment_amounts': [],
            'project_sizes': [],
            'savings_amounts': [],
            'time_periods': [],
        }
        
        # 投资额模式（美元）
        investment_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+million',  # $10 million
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+billion',  # $1 billion
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+million\s+dollars',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+billion\s+dollars',
        ]
        
        # 项目规模模式（MW, kW）
        size_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+MW',  # 10 MW
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+megawatts',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+kW',   # 100 kW
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+kilowatts',
        ]
        
        # 提取投资额
        for pattern in investment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers_info['investment_amounts'].extend(matches)
        
        # 提取项目规模
        for pattern in size_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers_info['project_sizes'].extend(matches)
        
        # 去重
        for key in numbers_info:
            numbers_info[key] = list(set(numbers_info[key]))
        
        return numbers_info
    
    def validate_commercial_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """验证工商业光伏文章"""
        validation = {
            'valid': True,
            'issues': [],
            'suggestions': [],
            'commercial_score': 0.0,
        }
        
        # 基础验证
        base_validation = super().validate_article(article)
        if not base_validation['valid']:
            validation['valid'] = False
            validation['issues'].extend(base_validation['issues'])
            validation['suggestions'].extend(base_validation['suggestions'])
        
        # 工商业光伏相关度验证
        if 'commercial_analysis' in article:
            analysis = article['commercial_analysis']
            validation['commercial_score'] = analysis.get('commercial_relevance_score', 0.0)
            
            if not analysis['is_commercial_solar']:
                validation['issues'].append('Not commercial solar content')
                validation['suggestions'].append('May not be relevant to commercial solar')
            
            if validation['commercial_score'] < 1.0:
                validation['issues'].append('Low commercial solar relevance score')
                validation['suggestions'].append('Content may not be focused on commercial solar')
        else:
            validation['issues'].append('No commercial analysis performed')
            validation['valid'] = False
        
        return validation