#!/usr/bin/env python3
"""
Main entry point for newsup-solar news aggregator.
支持普通模式和工商业光伏专项模式。
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
from src.storage.database import DatabaseManager
from src.processors.cleaner import ArticleCleaner
from src.processors.commercial_cleaner import CommercialSolarCleaner
from src.processors.classifier import ArticleClassifier

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_crawlers(commercial_mode: bool = False) -> List[BaseCrawler]:
    """Initialize and return configured crawlers."""
    if commercial_mode:
        logger.info("Using commercial solar crawlers")
        return [
            PVMagazineBusinessCrawler(),
            SolarPowerWorldCommercialCrawler(),
            # 可以添加更多商业爬虫
        ]
    else:
        logger.info("Using general solar crawlers")
        return [
            PVMagazineCrawler(),
            SolarPowerWorldCrawler(),
            # Add more crawlers here
        ]


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


async def process_articles(articles: List[dict], db_manager: DatabaseManager, commercial_mode: bool = False):
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
    
    processed_count = 0
    for article in articles:
        try:
            # Clean article content
            cleaned = cleaner.clean(article)
            
            # Classify article
            classified = classifier.classify(cleaned)
            
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
        "--source",
        type=str,
        default="all",
        help="Specific source to crawl: pv_magazine, solar_power_world, commercial, or all"
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
        # Get crawlers based on mode
        commercial_mode = args.commercial
        crawlers = get_crawlers(commercial_mode)
        
        # 如果指定了特定源，过滤爬虫
        if args.source != "all":
            filtered_crawlers = []
            source_map = {
                'pv_magazine': ['PVMagazineCrawler', 'PVMagazineBusinessCrawler'],
                'solar_power_world': ['SolarPowerWorldCrawler', 'SolarPowerWorldCommercialCrawler'],
                'commercial': ['PVMagazineBusinessCrawler', 'SolarPowerWorldCommercialCrawler'],
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
        await process_articles(articles, db_manager, commercial_mode)
        
        logger.info("Crawling completed")
    
    elif args.process:
        # TODO: Implement processing of existing articles
        logger.info("Processing existing articles...")
        # This would involve fetching unprocessed articles from DB
        # and running them through the processing pipeline
        pass
    
    elif args.serve:
        # Start API server
        from src.api.server import start_server
        await start_server()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())