"""
Creator Scraping Service
Orchestrates YouTube scraping, embedding generation, and database storage
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.intelligence.youtube_scraper import youtube_scraper
from app.services.intelligence.embedding_service import embedding_service
from app.services.intelligence.vector_store import vector_store

logger = logging.getLogger(__name__)


class CreatorScraper:
    """
    Orchestrates the full creator scraping pipeline:
    1. Search YouTube for channels
    2. Get channel details and videos
    3. Generate embeddings
    4. Save to database
    5. Build FAISS index
    """
    
    def __init__(self):
        self.scraped_creators = []
    
    def scrape_niche(
        self, 
        niche: str, 
        keywords: List[str], 
        max_per_keyword: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Scrape creators for a specific niche.
        
        Args:
            niche: Niche name (e.g., "tech", "fitness")
            keywords: Search keywords for this niche
            max_per_keyword: Max channels per keyword
            
        Returns:
            List of scraped creator data
        """
        logger.info(f"Scraping niche: {niche} with {len(keywords)} keywords")
        
        creators = []
        seen_ids = set()
        
        for keyword in keywords:
            logger.info(f"Searching for: {keyword}")
            
            # Search for channels
            channels = youtube_scraper.search_channels(keyword, max_results=max_per_keyword)
            
            for channel in channels:
                channel_id = channel['id']
                
                # Skip duplicates
                if channel_id in seen_ids:
                    continue
                seen_ids.add(channel_id)
                
                # Get full details
                details = youtube_scraper.get_channel_details(channel_id)
                if not details:
                    continue
                
                # Get recent videos
                videos = youtube_scraper.get_recent_videos(channel_id, max_results=10)
                
                # Extract content corpus
                corpus = youtube_scraper.extract_content_corpus(details, videos)
                
                # Generate embedding
                embedding = embedding_service.encode_text(corpus)
                
                # Infer tags from content
                tags = self._extract_tags(corpus, niche)
                
                # Build creator data
                creator_data = {
                    'id': channel_id,
                    'platform': 'youtube',
                    'name': details['name'],
                    'handle': details.get('custom_url', f"@{details['name'].lower().replace(' ', '')}"),
                    'bio': details['description'],
                    'subscriber_count': details['subscriber_count'],
                    'language': details.get('country', 'en'),
                    'niche': niche,
                    'embedding': embedding.tolist(),
                    'content_samples': [v['title'] for v in videos],
                    'tags': tags,
                    'metadata': {
                        'video_count': details['video_count'],
                        'view_count': details['view_count'],
                        'keywords': details.get('keywords', ''),
                        'thumbnail': details.get('thumbnail', '')
                    }
                }
                
                creators.append(creator_data)
                logger.info(f"Scraped: {details['name']} ({details['subscriber_count']:,} subs)")
        
        logger.info(f"Scraped {len(creators)} creators for niche: {niche}")
        self.scraped_creators.extend(creators)
        return creators
    
    def _extract_tags(self, corpus: str, niche: str) -> List[str]:
        """
        Extract relevant tags from content corpus.
        
        Args:
            corpus: Text content
            niche: Creator niche
            
        Returns:
            List of tags
        """
        tags = [niche]
        
        corpus_lower = corpus.lower()
        
        # Tech tags
        tech_keywords = {
            'coding': ['coding', 'programming', 'code'],
            'javascript': ['javascript', 'js', 'react', 'node'],
            'python': ['python', 'django', 'flask'],
            'web-development': ['web dev', 'frontend', 'backend'],
            'tutorials': ['tutorial', 'learn', 'course'],
            'reviews': ['review', 'comparison', 'vs'],
        }
        
        # Fitness tags
        fitness_keywords = {
            'bodybuilding': ['bodybuilding', 'muscle', 'gains'],
            'training': ['training', 'workout', 'exercise'],
            'nutrition': ['nutrition', 'diet', 'protein'],
            'science-based': ['science', 'research', 'study'],
        }
        
        # Finance tags
        finance_keywords = {
            'investing': ['invest', 'stocks', 'portfolio'],
            'real-estate': ['real estate', 'property', 'rental'],
            'passive-income': ['passive income', 'side hustle'],
            'frugal': ['frugal', 'saving', 'budget'],
        }
        
        # Combine all
        all_keywords = {**tech_keywords, **fitness_keywords, **finance_keywords}
        
        # Check for matches
        for tag, keywords in all_keywords.items():
            if any(kw in corpus_lower for kw in keywords):
                tags.append(tag)
        
        return tags[:6]  # Limit to 6 tags
    
    def scrape_all_niches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape creators across all major niches.
        
        Returns:
            Dictionary of niche -> creators
        """
        niche_config = {
            'tech': [
                'programming tutorials',
                'web development',
                'software engineering',
                'coding for beginners'
            ],
            'fitness': [
                'fitness training',
                'bodybuilding',
                'workout routines',
                'gym tips'
            ],
            'finance': [
                'personal finance',
                'investing for beginners',
                'stock market',
                'real estate investing'
            ],
            'gaming': [
                'gaming',
                'let\'s play',
                'game reviews',
                'esports'
            ],
            'lifestyle': [
                'vlogging',
                'minimalism',
                'lifestyle',
                'daily routines'
            ]
        }
        
        results = {}
        
        for niche, keywords in niche_config.items():
            creators = self.scrape_niche(niche, keywords, max_per_keyword=10)
            results[niche] = creators
        
        return results
    
    def get_scraped_count(self) -> int:
        """Get total number of scraped creators"""
        return len(self.scraped_creators)
    
    def get_quota_status(self) -> Dict[str, int]:
        """Get YouTube API quota status"""
        return youtube_scraper.get_quota_status()


# Global instance
creator_scraper = CreatorScraper()
