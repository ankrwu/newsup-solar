"""
Article cleaning and text processing.
"""

import re
import html
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ArticleCleaner:
    """Clean and normalize article content."""
    
    def __init__(self):
        # Common patterns to remove
        self.unwanted_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'<style.*?>.*?</style>',    # Style tags
            r'<!--.*?-->',               # HTML comments
            r'ADVERTISEMENT',            # Advertisements
            r'Sponsored.*',              # Sponsored content markers
            r'Sign up for.*',            # Newsletter signup prompts
            r'Read more:.*',             # Read more links
            r'Continue reading.*',       # Continue reading prompts
            r'Photo:.*',                 # Photo credits
            r'Image:.*',                 # Image credits
            r'Credit:.*',                # Credits
            r'Follow us on.*',           # Social media prompts
            r'Share this article.*',     # Sharing prompts
            r'\s+',                      # Multiple spaces (will be handled separately)
        ]
        
        # Solar power related terms for validation
        self.solar_keywords = [
            'solar', 'photovoltaic', 'pv', 'renewable', 'clean energy',
            'solar panel', 'solar installation', 'solar farm', 'solar project',
            'solar power', 'solar energy', 'rooftop solar', 'utility-scale',
            'energy storage', 'battery', 'grid', 'electricity', 'power plant',
            'climate', 'carbon', 'emissions', 'sustainability', 'green energy'
        ]
    
    def clean(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Clean article content and metadata."""
        cleaned = article.copy()
        
        # Clean title
        if 'title' in cleaned:
            cleaned['title'] = self._clean_text(cleaned['title'])
        
        # Clean content
        if 'content' in cleaned:
            cleaned['content'] = self._clean_content(cleaned['content'])
        
        # Clean summary
        if 'summary' in cleaned:
            cleaned['summary'] = self._clean_text(cleaned['summary'])
        
        # Clean author
        if 'author' in cleaned:
            cleaned['author'] = self._clean_author(cleaned['author'])
        
        # Validate solar relevance
        cleaned['relevance_score'] = self._calculate_relevance(cleaned)
        
        # Add cleaning metadata
        cleaned['metadata']['cleaned'] = True
        cleaned['metadata']['cleaning_timestamp'] = self._get_timestamp()
        
        logger.debug(f"Cleaned article: {cleaned.get('title', 'Unknown')}")
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove unwanted patterns
        for pattern in self.unwanted_patterns[:6]:  # First 6 are regex patterns
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim and normalize
        text = text.strip()
        
        # Remove trailing punctuation issues
        text = re.sub(r'[.,;:\s]+$', '', text)
        
        return text
    
    def _clean_content(self, content: str) -> str:
        """Clean article content with special handling."""
        if not content:
            return ""
        
        # Basic cleaning
        content = self._clean_text(content)
        
        # Remove very short paragraphs/sentences (likely noise)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Filter out very short or likely irrelevant sentences
        filtered_sentences = []
        for sentence in sentences:
            if len(sentence.split()) >= 4:  # At least 4 words
                # Check if sentence contains solar-related terms
                if any(keyword.lower() in sentence.lower() for keyword in self.solar_keywords[:10]):
                    filtered_sentences.append(sentence)
                elif len(sentence.split()) >= 8:  # Longer sentences might be relevant
                    filtered_sentences.append(sentence)
        
        # Reconstruct content
        cleaned_content = '. '.join(filtered_sentences)
        if cleaned_content and not cleaned_content.endswith('.'):
            cleaned_content += '.'
        
        return cleaned_content
    
    def _clean_author(self, author: str) -> str:
        """Clean and normalize author name."""
        if not author:
            return ""
        
        # Remove prefixes
        author = re.sub(r'^By\s+', '', author, flags=re.IGNORECASE)
        author = re.sub(r'^Written by\s+', '', author, flags=re.IGNORECASE)
        author = re.sub(r'^Author:\s+', '', author, flags=re.IGNORECASE)
        
        # Remove suffixes
        author = re.sub(r'\s*,\s*Contributor$', '', author, flags=re.IGNORECASE)
        author = re.sub(r'\s*,\s*Editor$', '', author, flags=re.IGNORECASE)
        author = re.sub(r'\s*\(.*\)$', '', author)
        
        # Clean up
        author = author.strip()
        
        return author
    
    def _calculate_relevance(self, article: Dict[str, Any]) -> float:
        """Calculate relevance score for solar power content."""
        relevance_score = 0.0
        
        # Check title
        title = article.get('title', '').lower()
        if title:
            for keyword in self.solar_keywords:
                if keyword.lower() in title:
                    relevance_score += 2.0  # Title matches are important
        
        # Check content
        content = article.get('content', '').lower()
        if content:
            keyword_count = 0
            for keyword in self.solar_keywords:
                if keyword.lower() in content:
                    keyword_count += 1
            
            # Normalize by content length and keyword count
            word_count = len(content.split())
            if word_count > 0:
                relevance_score += min(keyword_count * 10.0 / max(word_count, 100), 5.0)
        
        # Check keywords
        keywords = article.get('keywords', [])
        if keywords:
            keyword_matches = sum(1 for kw in keywords if any(
                solar_kw.lower() in str(kw).lower() for solar_kw in self.solar_keywords
            ))
            relevance_score += keyword_matches * 1.0
        
        # Normalize to 0-10 scale
        relevance_score = min(relevance_score, 10.0)
        
        return round(relevance_score, 2)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def validate_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Validate article structure and content."""
        validation = {
            'valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Check required fields
        required_fields = ['title', 'url', 'source', 'content']
        for field in required_fields:
            if not article.get(field):
                validation['valid'] = False
                validation['issues'].append(f'Missing required field: {field}')
        
        # Check content length
        content = article.get('content', '')
        if len(content.split()) < 20:
            validation['issues'].append('Content is too short (< 20 words)')
            validation['suggestions'].append('Consider including more detail or context')
        
        # Check relevance
        relevance = article.get('relevance_score', 0)
        if relevance < 1.0:
            validation['issues'].append('Low relevance score for solar power topic')
            validation['suggestions'].append('Article may not be primarily about solar power')
        
        # Check for duplicate content indicators
        title = article.get('title', '')
        if title and content:
            if title.lower() in content.lower() and len(content.split()) < 50:
                validation['issues'].append('Content may be duplicated from title')
        
        return validation