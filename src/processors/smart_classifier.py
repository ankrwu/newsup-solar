"""
智能分类系统
使用关键词匹配和规则引擎进行内容分类
支持中英文内容
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型枚举"""
    NEWS = "news"               # 新闻资讯
    POLICY = "policy"           # 政策法规
    MARKET = "market"           # 市场分析
    TECHNOLOGY = "technology"   # 技术创新
    PROJECT = "project"         # 项目动态
    FINANCE = "finance"         # 金融投资
    OPINION = "opinion"         # 观点评论
    GENERAL = "general"         # 通用


class MarketSegment(Enum):
    """市场细分"""
    RESIDENTIAL = "residential"     # 户用
    COMMERCIAL = "commercial"       # 工商业
    UTILITY = "utility"             # 公用事业/大型地面电站
    COMMUNITY = "community"         # 社区太阳能
    AGRIVOLTAIC = "agrivoltaic"     # 农光互补
    FLOATING = "floating"           # 漂浮光伏


@dataclass
class ClassificationResult:
    """分类结果"""
    content_type: ContentType
    market_segments: List[MarketSegment]
    confidence: float
    keywords_found: List[str]
    tags: List[str]
    language: str  # 'zh' or 'en'
    

class SmartClassifier:
    """智能分类器"""
    
    def __init__(self):
        self._init_keywords()
        self._init_rules()
    
    def _init_keywords(self):
        """初始化关键词"""
        # 内容类型关键词
        self.type_keywords = {
            ContentType.POLICY: {
                'zh': [
                    '政策', '法规', '法律', '条例', '规定', '办法',
                    '补贴', '补贴政策', '上网电价', '税收优惠', '税收抵免',
                    '配额制', '可再生能源配额', '强制配储',
                    '发改委', '能源局', '工信部', '住建部',
                    '十四五', '十五五', '规划', '行动计划',
                    '碳达峰', '碳中和', '双碳',
                ],
                'en': [
                    'policy', 'regulation', 'law', 'mandate', 'requirement',
                    'tax credit', 'ITC', 'PTC', 'incentive', 'subsidy',
                    'rebate', 'feed-in tariff', 'net metering',
                    'government', 'federal', 'state policy',
                    'carbon neutral', 'climate goal',
                ]
            },
            ContentType.MARKET: {
                'zh': [
                    '市场', '行业分析', '市场报告', '市场规模',
                    '增长率', '市场份额', '装机量', '装机容量',
                    '价格走势', '价格趋势', '成本下降',
                    '预测', '展望', '前景',
                    '吉瓦', '兆瓦', 'GW', 'MW',
                ],
                'en': [
                    'market', 'industry', 'analysis', 'report', 'forecast',
                    'growth', 'capacity', 'installation', 'shipment',
                    'market share', 'market size', 'trend',
                    'outlook', 'projection', 'statistics',
                    'GW', 'MW', 'gigawatt', 'megawatt',
                ]
            },
            ContentType.TECHNOLOGY: {
                'zh': [
                    '技术', '创新', '研发', '突破', '专利',
                    '效率', '转换效率', '电池效率', '组件效率',
                    '钙钛矿', 'TOPCon', 'HJT', '异质结',
                    '双面', '双玻', '叠瓦', '半片',
                    'n型', 'p型', '单晶', '多晶',
                    '逆变器', '储能系统', '跟踪支架',
                ],
                'en': [
                    'technology', 'innovation', 'R&D', 'breakthrough', 'patent',
                    'efficiency', 'cell efficiency', 'module efficiency',
                    'perovskite', 'TOPCon', 'HJT', 'heterojunction',
                    'bifacial', 'dual-glass', 'half-cut', 'shingled',
                    'n-type', 'p-type', 'monocrystalline', 'polycrystalline',
                    'inverter', 'storage system', 'tracker',
                ]
            },
            ContentType.PROJECT: {
                'zh': [
                    '项目', '电站', '光伏电站', '太阳能电站',
                    '开工', '竣工', '并网', '投运',
                    '签约', '签约仪式', '合作', '框架协议',
                    'EPC', '总承包', '建设', '安装',
                ],
                'en': [
                    'project', 'plant', 'solar farm', 'solar park',
                    'commission', 'grid-connected', 'operational',
                    'signed', 'agreement', 'partnership',
                    'EPC', 'construction', 'installation', 'completed',
                ]
            },
            ContentType.FINANCE: {
                'zh': [
                    '投资', '融资', '贷款', '基金',
                    'IPO', '上市', '股票', '股价',
                    '并购', '收购', '重组',
                    '融资租赁', 'PPA', '购电协议',
                    '收益率', 'IRR', '回报',
                    '亿元', '万美元', '亿美元',
                ],
                'en': [
                    'investment', 'financing', 'loan', 'fund', 'capital',
                    'IPO', 'stock', 'share', 'valuation',
                    'M&A', 'merger', 'acquisition', 'deal',
                    'PPA', 'power purchase agreement', 'lease',
                    'ROI', 'IRR', 'return', 'yield',
                    'billion', 'million', '$',
                ]
            },
            ContentType.OPINION: {
                'zh': [
                    '观点', '评论', '分析', '解读',
                    '专访', '采访', '对话', '访谈',
                    '认为', '表示', '指出', '预测',
                    '专家', '分析师', '负责人',
                ],
                'en': [
                    'opinion', 'commentary', 'analysis', 'insight',
                    'interview', 'exclusive', 'Q&A',
                    'says', 'believes', 'predicts', 'expects',
                    'expert', 'analyst', 'CEO', 'executive',
                ]
            },
        }
        
        # 市场细分关键词
        self.segment_keywords = {
            MarketSegment.RESIDENTIAL: {
                'zh': ['户用', '家庭', '住宅', '屋顶', '户用光伏', '家用'],
                'en': ['residential', 'home', 'rooftop', 'household', 'domestic'],
            },
            MarketSegment.COMMERCIAL: {
                'zh': ['工商业', '商业', '工业', '厂房', '仓库', '商场', '写字楼',
                       'C&I', '分布式', '工商业光伏'],
                'en': ['commercial', 'industrial', 'C&I', 'business', 'enterprise',
                       'warehouse', 'factory', 'office', 'retail'],
            },
            MarketSegment.UTILITY: {
                'zh': ['大型地面', '集中式', '公用事业', '大型光伏', '光伏基地',
                       '沙漠光伏', '戈壁', '风光大基地'],
                'en': ['utility', 'utility-scale', 'large-scale', 'solar farm',
                       'solar park', 'ground-mount', 'GW-scale'],
            },
            MarketSegment.COMMUNITY: {
                'zh': ['社区', '共享光伏', '村集体', '集中式扶贫'],
                'en': ['community solar', 'shared solar', 'solar garden'],
            },
            MarketSegment.AGRIVOLTAIC: {
                'zh': ['农光互补', '农光', '渔光互补', '林光互补', '光伏农业'],
                'en': ['agrivoltaic', 'agrisolar', 'farming', 'agricultural'],
            },
            MarketSegment.FLOATING: {
                'zh': ['漂浮', '水面光伏', '渔光', '水上光伏'],
                'en': ['floating', 'floatovoltaic', 'water-based'],
            },
        }
    
    def _init_rules(self):
        """初始化分类规则"""
        # 优先级规则：某些内容类型优先级更高
        self.type_priority = [
            ContentType.POLICY,      # 政策优先级最高
            ContentType.FINANCE,     # 金融次之
            ContentType.PROJECT,     # 项目动态
            ContentType.TECHNOLOGY,  # 技术
            ContentType.MARKET,      # 市场
            ContentType.OPINION,     # 观点
            ContentType.NEWS,        # 新闻
        ]
        
        # 组合规则：某些关键词组合表示特定类型
        self.combination_rules = [
            {
                'keywords': ['政策', '补贴'],
                'type': ContentType.POLICY,
                'weight': 2.0,
            },
            {
                'keywords': ['项目', 'MW', '并网'],
                'type': ContentType.PROJECT,
                'weight': 2.0,
            },
            {
                'keywords': ['技术', '效率', '突破'],
                'type': ContentType.TECHNOLOGY,
                'weight': 1.5,
            },
            {
                'keywords': ['投资', '融资', '亿元'],
                'type': ContentType.FINANCE,
                'weight': 1.5,
            },
        ]
    
    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        if not text:
            return 'en'
        
        # 统计中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return 'zh'
        return 'en'
    
    def classify(self, text: str) -> ClassificationResult:
        """
        对文本进行分类
        
        Args:
            text: 待分类的文本（标题+内容）
        
        Returns:
            ClassificationResult: 分类结果
        """
        if not text:
            return ClassificationResult(
                content_type=ContentType.GENERAL,
                market_segments=[],
                confidence=0.0,
                keywords_found=[],
                tags=[],
                language='en'
            )
        
        # 检测语言
        language = self.detect_language(text)
        text_lower = text.lower()
        
        # 内容类型分类
        type_scores = self._score_content_types(text_lower, language)
        content_type = self._determine_content_type(type_scores)
        
        # 市场细分分类
        market_segments = self._classify_market_segments(text_lower, language)
        
        # 提取关键词
        keywords_found = self._extract_keywords(text_lower, language)
        
        # 生成标签
        tags = self._generate_tags(content_type, market_segments, keywords_found)
        
        # 计算置信度
        confidence = type_scores.get(content_type, 0.0)
        
        return ClassificationResult(
            content_type=content_type,
            market_segments=market_segments,
            confidence=confidence,
            keywords_found=keywords_found,
            tags=tags,
            language=language
        )
    
    def _score_content_types(self, text: str, language: str) -> Dict[ContentType, float]:
        """计算各内容类型的得分"""
        scores = {t: 0.0 for t in ContentType}
        
        for content_type, keywords in self.type_keywords.items():
            lang_keywords = keywords.get(language, keywords.get('en', []))
            
            for keyword in lang_keywords:
                if keyword.lower() in text:
                    scores[content_type] += 1.0
        
        # 应用组合规则
        for rule in self.combination_rules:
            if all(kw.lower() in text for kw in rule['keywords']):
                target_type = rule['type']
                scores[target_type] += rule['weight']
        
        return scores
    
    def _determine_content_type(self, scores: Dict[ContentType, float]) -> ContentType:
        """确定内容类型"""
        # 按优先级检查
        for content_type in self.type_priority:
            if scores.get(content_type, 0) > 0:
                return content_type
        
        # 如果没有匹配，返回通用类型
        return ContentType.GENERAL
    
    def _classify_market_segments(self, text: str, language: str) -> List[MarketSegment]:
        """分类市场细分"""
        segments = []
        
        for segment, keywords in self.segment_keywords.items():
            lang_keywords = keywords.get(language, keywords.get('en', []))
            
            for keyword in lang_keywords:
                if keyword.lower() in text:
                    segments.append(segment)
                    break
        
        return segments
    
    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 提取所有匹配的关键词
        for content_type, type_kw in self.type_keywords.items():
            lang_keywords = type_kw.get(language, type_kw.get('en', []))
            for keyword in lang_keywords:
                if keyword.lower() in text and keyword not in keywords:
                    keywords.append(keyword)
        
        # 限制数量
        return keywords[:10]
    
    def _generate_tags(self, content_type: ContentType, 
                       market_segments: List[MarketSegment],
                       keywords: List[str]) -> List[str]:
        """生成标签"""
        tags = []
        
        # 内容类型标签
        tags.append(f"type_{content_type.value}")
        
        # 市场细分标签
        for segment in market_segments:
            tags.append(f"segment_{segment.value}")
        
        # 关键词标签（前5个）
        for kw in keywords[:5]:
            tags.append(f"kw_{kw.lower().replace(' ', '_')}")
        
        return list(set(tags))


def classify_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    对文章进行分类
    
    Args:
        article: 文章字典，包含 title 和 content 字段
    
    Returns:
        带有分类信息的文章字典
    """
    classifier = SmartClassifier()
    
    # 合并标题和内容
    text = f"{article.get('title', '')} {article.get('content', '')}"
    
    # 分类
    result = classifier.classify(text)
    
    # 更新文章
    classified = article.copy()
    
    if 'metadata' not in classified:
        classified['metadata'] = {}
    
    classified['metadata']['classification'] = {
        'content_type': result.content_type.value,
        'market_segments': [s.value for s in result.market_segments],
        'confidence': result.confidence,
        'keywords': result.keywords_found,
        'language': result.language,
    }
    
    # 添加标签
    if 'tags' not in classified['metadata']:
        classified['metadata']['tags'] = []
    classified['metadata']['tags'].extend(result.tags)
    classified['metadata']['tags'] = list(set(classified['metadata']['tags']))
    
    return classified
