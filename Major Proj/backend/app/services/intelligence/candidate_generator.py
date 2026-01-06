"""
Candidate Generator
Generates 50-200 raw competitor candidates using multiple discovery paths

Discovery Paths:
- Path A: Hashtag Exploration
- Path B: Audio Exploration (limited on Instagram public API)
- Path C: Mention Graph
- Path D: Trending-in-Category (semantic similarity)
"""
import logging
from typing import List, Set, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.scrapers.hybrid_instagram_scraper import get_hybrid_instagram_scraper
from app.models.creator import Creator
from app.models.creator_post import CreatorPost

logger = logging.getLogger(__name__)


class CandidateGenerator:
    """
    Generates competitor candidates using multiple discovery paths.
    
    Philosophy:
    - Cast a wide net (50-200 candidates)
    - Use multiple discovery paths
    - Deduplicate aggressively
    - Filter out obvious non-matches
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scraper = get_hybrid_instagram_scraper()
    
    async def generate_candidates(
        self,
        user_id: str,
        username: str,
        target_count: int = 100
    ) -> List[str]:
        """
        Generate competitor candidates for a user.
        
        Args:
            user_id: User's creator ID
            username: User's Instagram username
            target_count: Target number of candidates to generate
        
        Returns:
            List of candidate creator IDs (usernames)
        """
        logger.info(f"Generating candidates for {username} (target: {target_count})")
        
        candidates: Set[str] = set()
        
        # Get user's posts for signal extraction
        # Note: Scraper is still sync for now, wrapping if needed or keeping sync if fast
        user_posts = self._get_user_posts(username)
        
        if not user_posts:
            logger.warning(f"No posts found for {username}, using limited discovery")
        
        # Path A: Hashtag Exploration (Playwright)
        # Extract hashtags first
        hashtags = self._extract_hashtags(user_posts)
        if hashtags:
            try:
                from app.services.instagram.playwright_client import PlaywrightClient
                from app.services.instagram.candidate_generator import PlaywrightCandidateGenerator
                
                # Initialize Playwright client
                # TODO: In production, reuse a global client instance
                client = PlaywrightClient(headless=True) 
                
                # Use Playwright Generator
                pg_gen = PlaywrightCandidateGenerator(client)
                hashtag_candidates = await pg_gen.generate(hashtags[:5], limit_per_tag=20)
                
                candidates.update(hashtag_candidates)
                logger.info(f"Path A (Hashtags/Playwright): Found {len(hashtag_candidates)} candidates")
                
                # Cleanup
                await client.stop()
                
            except Exception as e:
                logger.error(f"Playwright discovery failed: {e}")
        else:
             logger.info("No hashtags found for Path A")
        
        # Path B: Audio Exploration (limited for public API)
        # Skipping for now as Instagram doesn't provide public audio search
        
        # Path C: Mention Graph
        mention_candidates = self._discover_via_mentions(user_posts, limit=30)
        candidates.update(mention_candidates)
        logger.info(f"Path C (Mentions): Found {len(mention_candidates)} candidates")
        
        # Path D: Trending-in-Category (semantic similarity)
        # This requires embeddings - will use existing creators in DB
        semantic_candidates = self._discover_via_semantic_similarity(username, limit=30)
        candidates.update(semantic_candidates)
        logger.info(f"Path D (Semantic): Found {len(semantic_candidates)} candidates")
        
        # Remove self
        candidates.discard(username)
        candidates.discard(user_id)
        
        # Convert to list
        candidate_list = list(candidates)
        
        logger.info(f"Total unique candidates: {len(candidate_list)}")
        
        return candidate_list[:target_count]
    
    def _get_user_posts(self, username: str) -> List[Dict[str, Any]]:
        """Get user's recent posts"""
        try:
            posts = self.scraper.get_recent_posts(username, limit=30)
            return posts
        except Exception as e:
            logger.error(f"Failed to get posts for {username}: {e}")
            return []
    
    def _extract_hashtags(self, user_posts: List[Dict]) -> List[str]:
        """Extract top hashtags from user posts"""
        if not user_posts:
            return []
            
        hashtag_freq = {}
        for post in user_posts:
            for tag in post.get('hashtags', []):
                hashtag_freq[tag] = hashtag_freq.get(tag, 0) + 1
        
        # Sort by frequency
        top_hashtags = sorted(hashtag_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [tag for tag, _ in top_hashtags]

    # Deprecated: Old sync method
    # def _discover_via_hashtags(...)
    
    def _discover_via_mentions(self, user_posts: List[Dict], limit: int = 30) -> Set[str]:
        """
        Path C: Discover candidates via mention graph.
        
        Strategy:
        1. Extract @mentions from user's posts
        2. Get those accounts (1-hop)
        3. Optionally crawl their mentions (2-hop, limited)
        """
        candidates = set()
        
        if not user_posts:
            return candidates
        
        # Extract all mentions
        mentions = set()
        for post in user_posts:
            mentions.update(post.get('mentions', []))
        
        logger.info(f"Found {len(mentions)} unique mentions")
        
        # Add direct mentions
        candidates.update(list(mentions)[:limit])
        
        # Optionally: 2-hop crawl (crawl mentions of mentions)
        # Skipping for now to avoid rate limits
        
        return candidates
    
    def _discover_via_semantic_similarity(self, username: str, limit: int = 30) -> Set[str]:
        """
        Path D: Discover candidates via semantic similarity.
        
        Strategy:
        1. Get user's profile/bio
        2. Find similar creators in database (by embedding or niche)
        3. Filter by recent activity
        """
        candidates = set()
        
        try:
            # Get user profile
            profile = self.scraper.get_profile(username)
            
            if not profile:
                return candidates
            
            bio = profile.get('bio', '')
            category = profile.get('category', '')
            
            # Find similar creators in DB by niche or category
            # This is a simplified version - in production, use embeddings
            similar_creators = self.db.query(Creator).filter(
                Creator.niche == category
            ).limit(limit).all()
            
            for creator in similar_creators:
                if creator.handle and creator.handle != username:
                    candidates.add(creator.handle)
            
            logger.info(f"Found {len(candidates)} semantically similar creators")
            
        except Exception as e:
            logger.error(f"Failed semantic discovery for {username}: {e}")
            self.db.rollback() # Ensure session is clean
        
        return candidates
