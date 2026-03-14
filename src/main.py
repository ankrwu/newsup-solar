#!/usr/bin/env python3
"""
Main entry point for newsup-solar news aggregator.
支持普通模式、工商业光伏专项模式和中文源模式。
"""

import asyncio
import logging
import argparse
from typing import List, Optional

from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_crawlers(commercial_mode: bool = False, chinese_mode: bool = False) -> List[BaseCrawler]:
    """Initialize and return configured crawlers."""
    crawlers = []
    
    if chinese_mode:
        logger.info("Using Chinese solar crawlers")
        crawlers = [
            PVMagazineChinaCrawler(),
            BjxGuangfuCrawler(),
        ]
    elif commercial_mode:
        logger.info("Using commercial solar crawlers")
        crawlers = [
            PVMagazineBusinessCrawler(),
            SolarPowerWorldCommercialCrawler(),
        ]
    else:
        logger.info("Using general solar crawlers")
        crawlers = [
            PVMagazineCrawler(),
            SolarPowerWorldCrawler(),
        ]
    
    return crawlers


async def crawl_news(crawlers: List[BaseCrawler], db_manager: DatabaseManager):
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


async def process_articles(articles: List[dict], db_manager: DatabaseManager, 
                          commercial_mode: bool = False, use_smart_processing: bool = True):
    """Process and store crawled articles."""
    if not articles:
        logger.info("No articles to process")
        return
    
    logger.info(f"Processing {len(articles)} articles (commercial mode: {commercial_mode})...")
    
    # Initialize processors based on mode
    if commercial_mode:
        cleaner = CommercialSolarCleaner()
        logger.info("Using commercial solar cleaner")
    else:
        cleaner = ArticleCleaner()
        logger.info("Using general solar cleaner")
    
    classifier = ArticleClassifier()
    
    # Initialize smart processors
    summarizer = SmartSummarizer(prefer_llm=True) if use_smart_processing else None
    smart_classifier = SmartClassifier() if use_smart_processing else None
    
    processed_count = 0
    for article in articles:
        try:
            # Clean article content
            cleaned = cleaner.clean(article)
            
            # Generate smart summary if enabled
            if summarizer and use_smart_processing:
                original_content = cleaned.get('content', '')
                if len(original_content) > 200:
                    smart_summary = summarizer.summarize(original_content, max_length=200)
                    if 'metadata' not in cleaned:
                        cleaned['metadata'] = {}
                    cleaned['metadata']['smart_summary'] = smart_summary
                    # 如果原文没有摘要，使用智能摘要
                    if not cleaned.get('summary'):
                        cleaned['summary'] = smart_summary
            
            # Classify article (traditional)
            classified = classifier.classify(cleaned)
            
            # Smart classification if enabled
            if smart_classifier and use_smart_processing:
                classified = classify_article(classified)
            
            # Store in database
            await db_manager.save_article(classified)
            processed_count += 1
            
            # 如果是商业模式，进行额外验证
            if commercial_mode:
                validation = cleaner.validate_commercial_article(classified)
                if not validation['valid']:
                    logger.warning(f"Commercial article validation issues: {validation['issues']}")
            
        except Exception as e:
            logger.error(f"Error processing article {article.get('url', 'unknown')}: {e}")
    
    logger.info(f"Successfully processed {processed_count}/{len(articles)} articles")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Solar power news aggregator")
    parser.add_argument(
        "--crawl", 
        action="store_true", 
        help="Run news crawling"
    )
    parser.add_argument(
        "--process", 
        action="store_true", 
        help="Process existing articles in database"
    )
    parser.add_argument(
        "--serve", 
        action="store_true", 
        help="Start API server"
    )
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="Initialize database"
    )
    parser.add_argument(
        "--commercial",
        action="store_true",
        help="Use commercial solar mode (focus on commercial/industrial solar)"
    )
    parser.add_argument(
        "--chinese",
        action="store_true",
        help="Use Chinese news sources (PV Magazine China, 北极星光伏网等)"
    )
    parser.add_argument(
        "--no-smart",
        action="store_true",
        help="Disable smart processing (LLM summaries, AI classification)"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="all",
        help="Specific source to crawl: pv_magazine, solar_power_world, commercial, chinese, or all"
    )
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    if args.init_db:
        logger.info("Initializing database...")
        await db_manager.initialize()
        logger.info("Database initialized")
        return
    
    if args.crawl:
        # Determine mode
        commercial_mode = args.commercial
        chinese_mode = args.chinese
        use_smart = not args.no_smart
        
        # Get crawlers based on mode
        crawlers = get_crawlers(commercial_mode, chinese_mode)
        
        # 如果指定了特定源，过滤爬虫
        if args.source != "all":
            filtered_crawlers = []
            source_map = {
                'pv_magazine': ['PVMagazineCrawler', 'PVMagazineBusinessCrawler'],
                'solar_power_world': ['SolarPowerWorldCrawler', 'SolarPowerWorldCommercialCrawler'],
                'commercial': ['PVMagazineBusinessCrawler', 'SolarPowerWorldCommercialCrawler'],
                'chinese': ['PVMagazineChinaCrawler', 'BjxGuangfuCrawler'],
                'pv_magazine_china': ['PVMagazineChinaCrawler'],
                'bjx': ['BjxGuangfuCrawler'],
            }
            
            target_classes = source_map.get(args.source.lower(), [])
            for crawler in crawlers:
                if crawler.__class__.__name__ in target_classes:
                    filtered_crawlers.append(crawler)
            
            if filtered_crawlers:
                crawlers = filtered_crawlers
                logger.info(f"Filtered to {len(crawlers)} crawler(s) for source: {args.source}")
            else:
                logger.warning(f"No crawlers found for source: {args.source}, using all crawlers")
        
        # Crawl news
        articles = await crawl_news(crawlers, db_manager)
        
        # Process articles
        await process_articles(articles, db_manager, commercial_mode, use_smart)
        
        logger.info("Crawling completed")
    
    elif args.process:
        logger.info("Processing existing articles...")
        pass
    
    elif args.serve:
        from src.api.server import start_server
        await start_server()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())