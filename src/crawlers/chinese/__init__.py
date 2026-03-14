"""
中文新闻源爬虫
"""

from .pv_magazine_china import PVMagazineChinaCrawler
from .bjx_guangfu import BjxGuangfuCrawler

__all__ = [
    'PVMagazineChinaCrawler',
    'BjxGuangfuCrawler',
]
