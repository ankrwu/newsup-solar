"""
智能摘要生成模块
支持多种方式生成文章摘要：提取式、LLM API、本地模型
"""

import re
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """摘要生成器基类"""
    
    @abstractmethod
    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成摘要"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查摘要器是否可用"""
        pass


class ExtractiveSummarizer(BaseSummarizer):
    """提取式摘要器 - 基于关键句提取"""
    
    def __init__(self):
        self.sentence_weights = {
            'position': 0.3,      # 位置权重（开头和结尾更重要）
            'length': 0.2,        # 长度权重
            'keywords': 0.5,      # 关键词权重
        }
        
        # 太阳能/光伏领域关键词
        self.domain_keywords = {
            # 中文关键词
            '光伏', '太阳能', '太阳能发电', '光伏发电', '光伏组件', '光伏电池',
            '太阳能电池', '太阳能电池板', '逆变器', '储能', '电池储能',
            '分布式光伏', '集中式光伏', '工商业光伏', '户用光伏',
            '光伏电站', '太阳能电站', '光伏项目', '光伏装机',
            '光伏产业链', '多晶硅', '硅片', '电池片', '组件',
            '碳中和', '清洁能源', '可再生能源', '新能源',
            '电力', '电网', '并网', '离网', '微电网',
            'PPA', '电价', '补贴', '税收优惠', '上网电价',
            # 英文关键词
            'solar', 'photovoltaic', 'PV', 'renewable', 'clean energy',
            'solar panel', 'inverter', 'battery storage', 'energy storage',
            'grid', 'utility', 'commercial', 'industrial', 'residential',
            'PPA', 'power purchase agreement', 'ITC', 'tax credit',
        }
    
    def is_available(self) -> bool:
        """始终可用"""
        return True
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成提取式摘要"""
        if not text or len(text) < max_length:
            return text
        
        # 分句
        sentences = self._split_sentences(text)
        if len(sentences) <= 2:
            return text[:max_length]
        
        # 计算每个句子的得分
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, i, len(sentences))
            scored_sentences.append((score, i, sentence))
        
        # 按得分排序
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        # 选择高分句子，保持原顺序
        selected = []
        total_length = 0
        for score, idx, sentence in scored_sentences:
            if total_length + len(sentence) <= max_length:
                selected.append((idx, sentence))
                total_length += len(sentence)
            if total_length >= max_length * 0.8:
                break
        
        # 按原顺序排列
        selected.sort(key=lambda x: x[0])
        
        return '。'.join([s[1] for s in selected]) + ('。' if selected else '')
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 中文和英文分句
        sentences = re.split(r'[。！？.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    
    def _score_sentence(self, sentence: str, position: int, total: int) -> float:
        """计算句子得分"""
        score = 0.0
        
        # 位置权重 - 开头和结尾更重要
        if position < 3:
            score += self.sentence_weights['position'] * (1.0 - position * 0.2)
        elif position >= total - 2:
            score += self.sentence_weights['position'] * 0.5
        
        # 长度权重 - 适中长度更好
        length = len(sentence)
        if 20 <= length <= 100:
            score += self.sentence_weights['length']
        elif length > 100:
            score += self.sentence_weights['length'] * 0.5
        
        # 关键词权重
        sentence_lower = sentence.lower()
        keyword_count = sum(1 for kw in self.domain_keywords if kw.lower() in sentence_lower)
        score += self.sentence_weights['keywords'] * min(keyword_count * 0.2, 1.0)
        
        # 包含数字加分（通常包含重要数据）
        if re.search(r'\d+\.?\d*\s*(MW|GW|kW|MW|亿元|万美元|%|吉瓦|兆瓦)', sentence):
            score += 0.3
        
        return score


class LLMSummarizer(BaseSummarizer):
    """LLM API 摘要器 - 支持多种 API"""
    
    def __init__(self, api_type: str = 'openai', api_key: str = None, model: str = None):
        self.api_type = api_type
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self._client = None
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        defaults = {
            'openai': 'gpt-3.5-turbo',
            'deepseek': 'deepseek-chat',
            'zhipu': 'glm-4-flash',
        }
        return defaults.get(self.api_type, 'gpt-3.5-turbo')
    
    def is_available(self) -> bool:
        """检查 API 是否可用"""
        import os
        if self.api_key:
            return True
        
        # 检查环境变量
        env_keys = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'zhipu': 'ZHIPU_API_KEY',
        }
        return bool(os.getenv(env_keys.get(self.api_type, 'OPENAI_API_KEY')))
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """使用 LLM 生成摘要"""
        if not self.is_available():
            logger.warning("LLM API not available, falling back to extractive summarizer")
            return ExtractiveSummarizer().summarize(text, max_length)
        
        try:
            if self.api_type == 'openai':
                return self._summarize_openai(text, max_length)
            elif self.api_type == 'deepseek':
                return self._summarize_deepseek(text, max_length)
            elif self.api_type == 'zhipu':
                return self._summarize_zhipu(text, max_length)
            else:
                return self._summarize_openai(text, max_length)
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return ExtractiveSummarizer().summarize(text, max_length)
    
    def _summarize_openai(self, text: str, max_length: int) -> str:
        """使用 OpenAI API"""
        import os
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_key or os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的太阳能/光伏行业新闻摘要助手。请用简洁的语言总结文章要点，突出关键数据和政策信息。"},
                {"role": "user", "content": f"请用{max_length}字以内总结以下太阳能行业新闻：\n\n{text[:2000]}"}
            ],
            max_tokens=max_length * 2,
            temperature=0.3,
        )
        
        return response.choices[0].message.content.strip()
    
    def _summarize_deepseek(self, text: str, max_length: int) -> str:
        """使用 DeepSeek API"""
        import os
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key or os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的太阳能/光伏行业新闻摘要助手。"},
                {"role": "user", "content": f"请用{max_length}字以内总结：\n\n{text[:2000]}"}
            ],
            max_tokens=max_length * 2,
        )
        
        return response.choices[0].message.content.strip()
    
    def _summarize_zhipu(self, text: str, max_length: int) -> str:
        """使用智谱 API"""
        import os
        from zhipuai import ZhipuAI
        
        client = ZhipuAI(api_key=self.api_key or os.getenv('ZHIPU_API_KEY'))
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": f"请用{max_length}字以内总结以下太阳能行业新闻：\n\n{text[:2000]}"}
            ],
        )
        
        return response.choices[0].message.content.strip()


class SmartSummarizer:
    """智能摘要器 - 自动选择最佳摘要方式"""
    
    def __init__(self, prefer_llm: bool = True, llm_type: str = 'openai'):
        self.extractive = ExtractiveSummarizer()
        self.llm = LLMSummarizer(api_type=llm_type) if prefer_llm else None
        self.prefer_llm = prefer_llm
    
    def summarize(self, text: str, max_length: int = 200, force_extractive: bool = False) -> str:
        """
        生成智能摘要
        
        Args:
            text: 原文文本
            max_length: 最大长度
            force_extractive: 强制使用提取式摘要
        """
        if not text:
            return ""
        
        # 如果原文很短，直接返回
        if len(text) <= max_length:
            return text
        
        # 优先使用 LLM
        if self.prefer_llm and self.llm and self.llm.is_available() and not force_extractive:
            return self.llm.summarize(text, max_length)
        
        # 回退到提取式
        return self.extractive.summarize(text, max_length)
    
    def batch_summarize(self, texts: List[str], max_length: int = 200) -> List[str]:
        """批量生成摘要"""
        return [self.summarize(text, max_length) for text in texts]


def get_summarizer(use_llm: bool = True, llm_type: str = 'openai') -> SmartSummarizer:
    """获取摘要器实例"""
    return SmartSummarizer(prefer_llm=use_llm, llm_type=llm_type)
