#!/usr/bin/env python3
"""
Main entry point for newsup-solar news aggregator.
"""

import asyncio
import logging
import argparse
from typing import List, Optional

from dotenv import load_dotenv

from src.crawlers.base import BaseCrawler
from src.crawlers.pv_magazine import PVMagazineCrawler
from src.crawlers.solar_power_world import SolarPowerWorldCrawler
from src.storage.database import DatabaseManager
from src.processors.cleaner import ArticleCleaner
from src.processors.classifier import ArticleClassifier

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_crawlers() -> List[BaseCrawler]:
    """Initialize and return configured crawlers."""
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
            logger.info(f"Crawling {crawler.source_name}...")
            articles = await crawler.crawl()
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles from {crawler.source_name}")
        except Exception as e:
            logger.error(f"Error crawling {crawler.source_name}: {e}")
    
    return all_articles


async def process_articles(articles: List[dict], db_manager: DatabaseManager):
    """Process and store crawled articles."""
    if not articles:
        logger.info("No articles to process")
        return
    
    logger.info(f"Processing {len(articles)} articles...")
    
    # Initialize processors
    cleaner = ArticleCleaner()
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
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    if args.init_db:
        logger.info("Initializing database...")
        await db_manager.initialize()
        logger.info("Database initialized")
        return
    
    if args.crawl:
        # Get crawlers
        crawlers = get_crawlers()
        
        # Crawl news
        articles = await crawl_news(crawlers, db_manager)
        
        # Process articles
        await process_articles(articles, db_manager)
        
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