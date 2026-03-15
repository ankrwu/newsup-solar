"""
中文新闻源爬虫
"""

from .pv_magazine_china import PVMagazineChinaCrawler
from .bjx_guangfu import BjxGuangfuCrawler
from .solarbe_crawler import SolarBECrawler
from .nengyuan_zazhi import NengYuanZaZhiCrawler
from .china_energy_news import ChinaEnergyNewsCrawler
from .solarzoom import SolarZoomCrawler
from .in_en_crawler import InEnCrawler
from .ofweek_solar import OfweekSolarCrawler
from .china_pv import ChinaPVCrawler
from .nea_crawler import NEACrawler
from .ditan_crawler import DiTanCrawler
from .company_crawlers import LongiCrawler, JASolarCrawler, TrinaSolarCrawler

__all__ = [
    'PVMagazineChinaCrawler',
    'BjxGuangfuCrawler',
    'SolarBECrawler',
    'NengYuanZaZhiCrawler',
    'ChinaEnergyNewsCrawler',
    'SolarZoomCrawler',
    'InEnCrawler',
    'OfweekSolarCrawler',
    'ChinaPVCrawler',
    'NEACrawler',
    'DiTanCrawler',
    'LongiCrawler',
    'JASolarCrawler',
    'TrinaSolarCrawler',
]
