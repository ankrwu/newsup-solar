"""
Database management for news articles.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
logger = logging.getLogger(__name__)


class Article(Base):
    """SQLAlchemy model for news articles."""
    
    __tablename__ = 'articles'
    
    # Primary key
    article_id = Column(String(64), primary_key=True)
    
    # Basic article info
    title = Column(Text, nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    source = Column(String(256), nullable=False)
    source_url = Column(String(2048))
    
    # Content
    content = Column(Text)
    summary = Column(Text)
    
    # Metadata
    author = Column(String(256))
    publish_date = Column(DateTime)
    crawl_date = Column(DateTime, default=datetime.utcnow)
    
    # Classification
    keywords = Column(JSON, default=list)
    categories = Column(JSON, default=list)
    
    # Analysis scores
    sentiment_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_date = Column(DateTime)
    
    # Raw data for debugging
    raw_html = Column(Text)
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary."""
        return {
            'article_id': self.article_id,
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'source_url': self.source_url,
            'author': self.author,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'crawl_date': self.crawl_date.isoformat() if self.crawl_date else None,
            'content': self.content,
            'summary': self.summary,
            'keywords': self.keywords,
            'categories': self.categories,
            'sentiment_score': self.sentiment_score,
            'relevance_score': self.relevance_score,
            'processed': self.processed,
            'processing_date': self.processing_date.isoformat() if self.processing_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseManager:
    """Manage database operations for news articles."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'sqlite:///./data/news.db'
        )
        self.engine = None
        self.Session = None
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            # Create data directory if using SQLite
            if 'sqlite' in self.database_url:
                os.makedirs('./data', exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=os.getenv('DEBUG', 'false').lower() == 'true'
            )
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info(f"Database initialized: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def save_article(self, article_data: Dict[str, Any]) -> bool:
        """Save an article to the database."""
        if not self.Session:
            await self.initialize()
        
        session = self.Session()
        try:
            # Check if article already exists
            existing = session.query(Article).filter_by(
                article_id=article_data.get('article_id')
            ).first()
            
            if existing:
                # Update existing article
                for key, value in article_data.items():
                    if hasattr(existing, key) and key not in ['article_id', 'created_at']:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                logger.debug(f"Updated article: {article_data.get('title')}")
            else:
                # Create new article
                article = Article(**article_data)
                session.add(article)
                logger.debug(f"Added new article: {article_data.get('title')}")
            
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving article: {e}")
            return False
        finally:
            session.close()
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get an article by ID."""
        if not self.Session:
            await self.initialize()
        
        session = self.Session()
        try:
            article = session.query(Article).filter_by(article_id=article_id).first()
            return article.to_dict() if article else None
        finally:
            session.close()
    
    async def get_articles(
        self, 
        limit: int = 100,
        offset: int = 0,
        source: Optional[str] = None,
        category: Optional[str] = None,
        processed: Optional[bool] = None,
        order_by: str = 'crawl_date',
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """Get articles with filtering and pagination."""
        if not self.Session:
            await self.initialize()
        
        session = self.Session()
        try:
            query = session.query(Article)
            
            # Apply filters
            if source:
                query = query.filter_by(source=source)
            if category:
                query = query.filter(Article.categories.contains([category]))
            if processed is not None:
                query = query.filter_by(processed=processed)
            
            # Apply ordering
            order_column = getattr(Article, order_by, Article.crawl_date)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
            
            # Apply pagination
            articles = query.offset(offset).limit(limit).all()
            
            return [article.to_dict() for article in articles]
            
        finally:
            session.close()
    
    async def delete_article(self, article_id: str) -> bool:
        """Delete an article by ID."""
        if not self.Session:
            await self.initialize()
        
        session = self.Session()
        try:
            article = session.query(Article).filter_by(article_id=article_id).first()
            if article:
                session.delete(article)
                session.commit()
                logger.info(f"Deleted article: {article_id}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting article: {e}")
            return False
        finally:
            session.close()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.Session:
            await self.initialize()
        
        session = self.Session()
        try:
            # Total articles
            total = session.query(Article).count()
            
            # Articles by source
            sources = session.query(
                Article.source,
                Article.processed,
                Article.crawl_date
            ).all()
            
            # Processed vs unprocessed
            processed = session.query(Article).filter_by(processed=True).count()
            
            # Recent articles (last 7 days)
            week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = week_ago.replace(day=week_ago.day-7)
            recent = session.query(Article).filter(Article.crawl_date >= week_ago).count()
            
            return {
                'total_articles': total,
                'processed_articles': processed,
                'unprocessed_articles': total - processed,
                'recent_articles_7d': recent,
                'sources': {s.source: s.count for s in sources} if hasattr(sources[0], 'count') else {},
            }
        finally:
            session.close()
    
    def __del__(self):
        """Cleanup database connection."""
        if self.engine:
            self.engine.dispose()