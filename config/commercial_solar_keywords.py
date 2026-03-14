"""
工商业光伏专项关键词配置
用于内容过滤、分类和识别
"""

# 核心工商业光伏关键词
COMMERCIAL_SOLAR_KEYWORDS = [
    # 基础术语
    'commercial solar',
    'industrial solar', 
    'C&I solar',
    'commercial PV',
    'industrial PV',
    'business solar',
    'commercial and industrial solar',
    
    # 项目类型
    'rooftop solar commercial',
    'solar for business',
    'solar for industry',
    'warehouse solar',
    'factory solar',
    'office building solar',
    'retail solar',
    'shopping center solar',
    'data center solar',
    'hospital solar',
    'school solar',
    'university solar',
    'municipal solar',
    'community solar commercial',
    
    # 商业模式
    'PPA',
    'power purchase agreement',
    'solar lease',
    'third-party ownership',
    'solar service agreement',
    'energy service agreement',
    'virtual PPA',
    'corporate PPA',
    'solar financing',
    'solar loan commercial',
    
    # 政策相关
    'investment tax credit',
    'ITC',
    'commercial solar rebate',
    'business solar incentive',
    'commercial net metering',
    'solar policy commercial',
    'business energy investment',
    'accelerated depreciation',
    'MACRS',
    'commercial solar grant',
    
    # 市场与分析
    'commercial solar market',
    'C&I solar market',
    'commercial solar growth',
    'business solar adoption',
    'commercial solar report',
    'solar installation cost commercial',
    'solar ROI business',
    'payback period commercial',
    'commercial solar economics',
    'solar savings business',
    
    # 技术相关
    'bifacial commercial',
    'solar tracker commercial',
    'energy storage commercial',
    'solar+storage commercial',
    'microgrid commercial',
    'smart solar commercial',
    'building-integrated PV',
    'BIPV commercial',
]

# 政策相关关键词（用于政策分类）
POLICY_KEYWORDS = [
    'policy',
    'regulation',
    'law',
    'bill',
    'act',
    'incentive',
    'subsidy',
    'tax credit',
    'rebate',
    'tariff',
    'standard',
    'mandate',
    'directive',
    'guideline',
    'framework',
    'program',
    'initiative',
    'funding',
    'grant',
    'finance',
]

# 市场相关关键词（用于市场分类）
MARKET_KEYWORDS = [
    'market',
    'report',
    'forecast',
    'outlook',
    'trend',
    'analysis',
    'research',
    'study',
    'data',
    'statistics',
    'growth',
    'decline',
    'expansion',
    'contraction',
    'price',
    'cost',
    'investment',
    'funding',
    'financing',
    'deal',
    'transaction',
    'M&A',
    'merger',
    'acquisition',
]

# 地域关键词（用于地域分类）
REGION_KEYWORDS = {
    'us': ['US', 'United States', 'America', 'federal', 'state', 'California', 'Texas', 'New York'],
    'china': ['China', 'Chinese', 'PRC', 'Beijing', 'Shanghai', 'Guangdong'],
    'europe': ['EU', 'Europe', 'European', 'Germany', 'UK', 'France', 'Spain', 'Italy'],
    'apac': ['APAC', 'Asia Pacific', 'Japan', 'Korea', 'Australia', 'India', 'Southeast Asia'],
}

# 项目规模关键词
PROJECT_SCALE_KEYWORDS = {
    'small': ['<100 kW', 'small-scale', 'rooftop', 'small commercial'],
    'medium': ['100 kW-1 MW', 'medium-scale', 'commercial', 'industrial'],
    'large': ['>1 MW', 'large-scale', 'utility-scale', 'solar farm', 'solar park'],
}

def is_commercial_solar_content(text: str) -> bool:
    """检查文本是否与工商业光伏相关"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 检查是否包含核心关键词
    for keyword in COMMERCIAL_SOLAR_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    return False

def classify_content_type(text: str) -> dict:
    """分类内容类型：新闻/政策/市场"""
    text_lower = text.lower()
    
    classification = {
        'is_news': False,
        'is_policy': False,
        'is_market': False,
        'keywords_found': [],
    }
    
    # 检查政策关键词
    for keyword in POLICY_KEYWORDS:
        if keyword.lower() in text_lower:
            classification['is_policy'] = True
            classification['keywords_found'].append(keyword)
    
    # 检查市场关键词
    for keyword in MARKET_KEYWORDS:
        if keyword.lower() in text_lower:
            classification['is_market'] = True
            classification['keywords_found'].append(keyword)
    
    # 如果不属于政策或市场，则归类为新闻
    if not (classification['is_policy'] or classification['is_market']):
        classification['is_news'] = True
    
    return classification

def extract_project_scale(text: str) -> str:
    """提取项目规模信息"""
    text_lower = text.lower()
    
    for scale, keywords in PROJECT_SCALE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return scale
    
    return 'unknown'

def extract_regions(text: str) -> list:
    """提取地域信息"""
    text_lower = text.lower()
    regions_found = []
    
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                regions_found.append(region)
                break  # 每个地区只添加一次
    
    return regions_found