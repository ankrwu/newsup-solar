#!/usr/bin/env python3
"""
solarnews - Solar power news aggregator CLI
一键获取全球太阳能行业新闻

Usage:
    solarnews crawl              # 爬取所有源（中英文）
    solarnews crawl --chinese    # 只爬中文源
    solarnews crawl --english    # 只爬英文源
    solarnews crawl --smart      # 启用智能摘要
    solarnews serve              # 启动 API 服务
    solarnews --help             # 显示帮助
"""

import asyncio
import logging
import argparse
import sys
from typing import List, Optional
from datetime import datetime

# 尝试导入项目模块
try:
    from src.crawlers.base import BaseCrawler
    from src.crawlers.pv_magazine import PVMagazineCrawler
    from src.crawlers.solar_power_world import SolarPowerWorldCrawler
    from src.crawlers.commercial.pv_magazine_business import PVMagazineBusinessCrawler
    from src.crawlers.commercial.solar_power_world_commercial import SolarPowerWorldCommercialCrawler
    from src.crawlers.chinese.pv_magazine_china import PVMagazineChinaCrawler
    from src.crawlers.chinese.bjx_guangfu import BjxGuangfuCrawler
    from src.storage.database import DatabaseManager
    from src.processors.cleaner import ArticleCleaner
    from src.processors.commercial_cleaner import CommercialSolarCleaner
    from src.processors.classifier import ArticleClassifier
    from src.processors.smart_summarizer import SmartSummarizer
    from src.processors.smart_classifier import SmartClassifier, classify_article
except ImportError:
    # 如果直接运行，添加项目根目录到路径
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.crawlers.base import BaseCrawler
    from src.crawlers.pv_magazine import PVMagazineCrawler
    from src.crawlers.solar_power_world import SolarPowerWorldCrawler
    from src.crawlers.commercial.pv_magazine_business import PVMagazineBusinessCrawler
    from src.crawlers.commercial.solar_power_world_commercial import SolarPowerWorldCommercialCrawler
    from src.crawlers.chinese.pv_magazine_china import PVMagazineChinaCrawler
    from src.crawlers.chinese.bjx_guangfu import BjxGuangfuCrawler
    from src.storage.database import DatabaseManager
    from src.processors.cleaner import ArticleCleaner
    from src.processors.commercial_cleaner import CommercialSolarCleaner
    from src.processors.classifier import ArticleClassifier
    from src.processors.smart_summarizer import SmartSummarizer
    from src.processors.smart_classifier import SmartClassifier, classify_article

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# 版本信息
__version__ = "1.0.0"
__author__ = "Solar News Team"


def get_crawlers(commercial_mode: bool = False, chinese_only: bool = False, 
                 english_only: bool = False, use_playwright: bool = False) -> List[BaseCrawler]:
    """
    Initialize and return configured crawlers.
    
    默认情况下（不指定任何参数）会同时爬取中英文源
    """
    crawlers = []
    
    if commercial_mode:
        logger.info("Using commercial solar crawlers")
        crawlers = [
            PVMagazineBusinessCrawler(),
            SolarPowerWorldCommercialCrawler(),
        ]
    elif chinese_only:
        logger.info("Using Chinese solar crawlers only")
        crawlers = [
            PVMagazineChinaCrawler(),
            BjxGuangfuCrawler(use_playwright=use_playwright),
        ]
    elif english_only:
        logger.info("Using English solar crawlers only")
        crawlers = [
            PVMagazineCrawler(use_playwright=use_playwright),
            SolarPowerWorldCrawler(use_playwright=use_playwright),
        ]
    else:
        logger.info("Using all solar crawlers (Chinese + English)")
        crawlers = [
            PVMagazineCrawler(use_playwright=use_playwright),
            SolarPowerWorldCrawler(use_playwright=use_playwright),
            PVMagazineChinaCrawler(),
            BjxGuangfuCrawler(use_playwright=use_playwright),
        ]
    
    return crawlers


async def crawl_news(crawlers: List[BaseCrawler]) -> List[dict]:
    """Crawl news from all sources."""
    logger.info("Starting news crawl...")
    
    all_articles = []
    for crawler in crawlers:
        try:
            logger.info(f"Crawling {crawler.source_display_name}...")
            articles = await crawler.crawl()
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles from {crawler.source_display_name}")
        except Exception as e:
            logger.error(f"Error crawling {crawler.source_display_name}: {e}")
    
    return all_articles


async def process_articles(articles: List[dict], commercial_mode: bool = False, 
                          use_smart: bool = False):
    """Process and store crawled articles."""
    if not articles:
        logger.info("No articles to process")
        return 0
    
    logger.info(f"Processing {len(articles)} articles...")
    
    # Initialize processors
    cleaner = CommercialSolarCleaner() if commercial_mode else ArticleCleaner()
    classifier = ArticleClassifier()
    summarizer = SmartSummarizer(prefer_llm=True) if use_smart else None
    smart_classifier = SmartClassifier() if use_smart else None
    
    # Initialize database
    db_manager = DatabaseManager()
    
    processed_count = 0
    for article in articles:
        try:
            cleaned = cleaner.clean(article)
            
            # Smart summary if enabled
            if summarizer and use_smart:
                content = cleaned.get('content', '')
                if len(content) > 200:
                    summary = summarizer.summarize(content, max_length=200)
                    if 'metadata' not in cleaned:
                        cleaned['metadata'] = {}
                    cleaned['metadata']['smart_summary'] = summary
                    if not cleaned.get('summary'):
                        cleaned['summary'] = summary
            
            # Classify
            classified = classifier.classify(cleaned)
            
            if smart_classifier and use_smart:
                classified = classify_article(classified)
            
            # Save to database
            await db_manager.save_article(classified)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
    
    logger.info(f"Successfully processed {processed_count}/{len(articles)} articles")
    return processed_count


async def run_crawl(args):
    """运行爬虫"""
    crawlers = get_crawlers(
        commercial_mode=args.commercial,
        chinese_only=args.chinese,
        english_only=args.english,
        use_playwright=args.playwright
    )
    
    articles = await crawl_news(crawlers)
    
    if articles:
        processed = await process_articles(
            articles, 
            commercial_mode=args.commercial,
            use_smart=args.smart
        )
        
        print(f"\n{'='*50}")
        print(f"爬取完成!")
        print(f"发现文章: {len(articles)} 篇")
        print(f"处理成功: {processed} 篇")
        print(f"{'='*50}\n")
    else:
        print("\n未发现新文章\n")


async def run_serve(args):
    """启动 API 服务"""
    try:
        from src.api.server import start_server
        print(f"\n启动 API 服务...")
        print(f"访问 http://localhost:8000 查看文档\n")
        await start_server()
    except ImportError:
        logger.error("API server module not found")
        sys.exit(1)


async def run_stats(args):
    """显示统计信息"""
    db_manager = DatabaseManager()
    stats = await db_manager.get_stats()
    
    print(f"\n{'='*50}")
    print("Solar News 统计信息")
    print(f"{'='*50}")
    print(f"总文章数: {stats.get('total', 0)}")
    print(f"今日新增: {stats.get('today', 0)}")
    print(f"中文文章: {stats.get('chinese', 0)}")
    print(f"英文文章: {stats.get('english', 0)}")
    print(f"{'='*50}\n")


def main():
    """Main entry point for solarnews CLI."""
    parser = argparse.ArgumentParser(
        prog="solarnews",
        description="🌞 Solar News - 全球太阳能行业新闻聚合器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  solarnews crawl                    爬取所有源（默认中英文）
  solarnews crawl --chinese          只爬取中文源
  solarnews crawl --english          只爬取英文源
  solarnews crawl --smart            启用智能摘要
  solarnews crawl --playwright       启用动态渲染
  solarnews crawl --commercial       只爬取工商业光伏新闻
  solarnews serve                    启动 API 服务
  solarnews stats                    显示统计信息

更多信息请访问: https://github.com/ankrwu/newsup-solar
        """
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取新闻')
    crawl_parser.add_argument('--chinese', action='store_true', help='只爬取中文源')
    crawl_parser.add_argument('--english', action='store_true', help='只爬取英文源')
    crawl_parser.add_argument('--commercial', action='store_true', help='只爬取工商业光伏新闻')
    crawl_parser.add_argument('--smart', action='store_true', help='启用智能摘要和分类')
    crawl_parser.add_argument('--playwright', action='store_true', help='启用动态渲染（较慢但更可靠）')
    crawl_parser.add_argument('--source', type=str, default='all', help='指定数据源')
    
    # serve 命令
    serve_parser = subparsers.add_parser('serve', help='启动 API 服务')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'crawl':
        asyncio.run(run_crawl(args))
    elif args.command == 'serve':
        asyncio.run(run_serve(args))
    elif args.command == 'stats':
        asyncio.run(run_stats(args))
    elif args.command == 'init':
        db_manager = DatabaseManager()
        asyncio.run(db_manager.initialize())
        print("\n✅ 数据库初始化完成\n")


if __name__ == "__main__":
    main()
