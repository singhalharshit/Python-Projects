"""
Semantic Competitor Discovery
Discovers competitors through content similarity, NOT Instagram scraping
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class SemanticCompetitorDiscovery:
    """
    Discovers competitors by:
    1. Encoding user's content semantics
    2. Searching open web for similar content
    3. Discovering creators indirectly
    4. Ranking by similarity
    5. Learning from user feedback
    
    NO Instagram scraping required.
    """
    
    def __init__(self, embedding_service, db=None):
        self.embedding_service = embedding_service
        self.db = db
        self.cache = {}
    
    def discover_competitors(
        self,
        username: str,
        bio: str,
        recent_captions: List[str],
        hashtags: List[str],
        language: str = "en",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Discover competitors through semantic analysis.
        
        Args:
            username: User's Instagram username
            bio: Account bio text
            recent_captions: 5-10 recent post captions
            hashtags: Hashtags the user frequently uses
            language: Content language
            limit: Number of competitors to return
        
        Returns:
            List of competitor profiles with semantic scores
        """
        logger.info(f"🧠 Semantic discovery for @{username}...")
        
        # Step 1: Encode user's content identity
        content_embedding = self._create_content_embedding(
            bio=bio,
            captions=recent_captions,
            hashtags=hashtags
        )
        
        logger.info(f"✅ Created content embedding (384-dim)")
        
        # Step 2: Map to open web (search for similar content)
        web_signals = self._search_open_web(
            embedding=content_embedding,
            bio=bio,
            captions=recent_captions,
            hashtags=hashtags
        )
        
        logger.info(f"✅ Found {len(web_signals)} web signals")
        
        # Step 3: Extract creator identities from web signals
        candidate_creators = self._extract_creators_from_web(
            web_signals
        )
        
        logger.info(f"✅ Extracted {len(candidate_creators)} candidate creators")
        
        # Step 4: Rank by semantic similarity + other factors
        ranked_competitors = self._rank_competitors(
            user_embedding=content_embedding,
            candidates=candidate_creators,
            user_bio=bio,
            user_hashtags=hashtags
        )
        
        logger.info(f"✅ Ranked competitors")
        
        # Step 5: Return top N with metadata
        top_competitors = ranked_competitors[:limit]
        
        logger.info(f"🎯 Returning {len(top_competitors)} competitors")
        
        return top_competitors
    
    def _create_content_embedding(
        self,
        bio: str,
        captions: List[str],
        hashtags: List[str]
    ) -> np.ndarray:
        """
        Create 384-dim embedding representing content identity.
        
        Example output:
        fitness · female · aesthetic · reels · workouts · motivation · diet
        """
        # Combine all text signals
        text_components = [
            bio,
            *captions,
            " ".join(hashtags)
        ]
        
        combined_text = " ".join(filter(None, text_components))
        
        # Encode with sentence-transformers
        embedding = self.embedding_service.encode_text(combined_text)
        
        return embedding
    
    def _search_open_web(
        self,
        embedding: np.ndarray,
        bio: str,
        captions: List[str],
        hashtags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search open web for similar content.
        
        Sources:
        - Google Trends
        - YouTube
        - Reddit
        - Google News
        - Public blogs
        
        Returns creator mentions, topics, channels.
        """
        signals = []
        
        # Extract semantic queries from content
        semantic_queries = self._generate_semantic_queries(bio, captions, hashtags)
        
        logger.info(f"  Generated {len(semantic_queries)} semantic queries")
        
        # Search each source
        for query in semantic_queries[:5]:  # Top 5 queries
            # YouTube search
            youtube_results = self._search_youtube(query)
            signals.extend(youtube_results)
            
            # Reddit search
            reddit_results = self._search_reddit(query)
            signals.extend(reddit_results)
            
            # Google Trends
            trends = self._search_google_trends(query)
            signals.extend(trends)
        
        return signals
    
    def _generate_semantic_queries(
        self,
        bio: str,
        captions: List[str],
        hashtags: List[str]
    ) -> List[str]:
        """
        Generate semantic search queries from content.
        
        Example:
        Input: "Fitness girl" + "#workout #gym #glutes"
        Output: [
            "home workout female aesthetic",
            "glute workout reels",
            "fitness motivation girls"
        ]
        """
        # Extract key themes
        all_text = f"{bio} {' '.join(captions)} {' '.join(hashtags)}"
        
        # Use simple keyword extraction for now
        # In production, use NLP (spaCy, TF-IDF, etc.)
        keywords = self._extract_keywords(all_text)
        
        # Generate query combinations
        queries = []
        
        # Fitness example
        if any(kw in all_text.lower() for kw in ['fitness', 'workout', 'gym']):
            queries.extend([
                "home workout fitness influencers",
                "gym workout content creators",
                "fitness motivation instagram",
                "workout tutorials youtube"
            ])
        
        # Add hashtag-based queries
        for hashtag in hashtags[:3]:
            clean_tag = hashtag.replace('#', '')
            queries.append(f"{clean_tag} content creators")
        
        return queries
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key themes from text"""
        # Simple keyword extraction
        # In production: use TF-IDF, TextRank, etc.
        
        common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but'}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        
        # Return top 10 by frequency
        from collections import Counter
        freq = Counter(keywords)
        return [word for word, _ in freq.most_common(10)]
    
    def _search_youtube(self, query: str) -> List[Dict[str, Any]]:
        """
        Search YouTube for similar content.
        Returns channel names, not metrics.
        """
        logger.info(f"  🔍 YouTube: {query}")
        
        # Use real API if available
        from app.services.web_search_service import get_web_search_service
        web_search = get_web_search_service()
        
        return web_search.search_youtube(query, max_results=5)
    
    def _search_reddit(self, query: str) -> List[Dict[str, Any]]:
        """Search Reddit for creator mentions"""
        logger.info(f"  🔍 Reddit: {query}")
        
        # Use real API if available
        from app.services.web_search_service import get_web_search_service
        web_search = get_web_search_service()
        
        return web_search.search_reddit(query, limit=5)
    
    def _search_google_trends(self, query: str) -> List[Dict[str, Any]]:
        """Get trending topics related to query"""
        logger.info(f"  🔍 Google Trends: {query}")
        
        # Use real API if available
        from app.services.web_search_service import get_web_search_service
        web_search = get_web_search_service()
        
        return web_search.search_google(query, num_results=5)
    
    def _extract_creators_from_web(
        self,
        web_signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract creator identities from web signals.
        
        Returns:
            List of creator profiles with source attribution
        """
        creators = {}
        
        for signal in web_signals:
            # Extract creator name
            creator_name = signal.get('creator_name')
            
            if creator_name and creator_name not in creators:
                creators[creator_name] = {
                    'username': creator_name,
                    'platform': signal.get('platform', 'instagram'),
                    'discovered_via': signal.get('source'),
                    'content_type': signal.get('content_type'),
                    'discovery_signals': 1
                }
            elif creator_name:
                # Increment signal count (found via multiple sources)
                creators[creator_name]['discovery_signals'] += 1
            
            # Also extract from related_creators
            if 'related_creators' in signal:
                for creator in signal['related_creators']:
                    if creator not in creators:
                        creators[creator] = {
                            'username': creator,
                            'platform': 'instagram',
                            'discovered_via': signal.get('source'),
                            'discovery_signals': 1
                        }
        
        return list(creators.values())
    
    def _rank_competitors(
        self,
        user_embedding: np.ndarray,
        candidates: List[Dict[str, Any]],
        user_bio: str,
        user_hashtags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Rank candidates by:
        - Semantic similarity
        - Discovery signal count
        - Platform overlap
        - Content type match
        """
        scored_candidates = []
        
        for candidate in candidates:
            # Create candidate embedding
            candidate_text = f"{candidate['username']} {candidate.get('content_type', '')}"
            candidate_embedding = self.embedding_service.encode_text(candidate_text)
            
            # Calculate semantic similarity
            semantic_score = float(np.dot(user_embedding, candidate_embedding) / 
                                 (np.linalg.norm(user_embedding) * np.linalg.norm(candidate_embedding)))
            
            # Discovery signal bonus (found via multiple sources = more relevant)
            signal_bonus = min(candidate.get('discovery_signals', 1) * 0.1, 0.3)
            
            # Platform match bonus
            platform_bonus = 0.2 if candidate.get('platform') == 'instagram' else 0
            
            # Total score
            total_score = semantic_score + signal_bonus + platform_bonus
            
            # Add to candidate
            candidate['scores'] = {
                'semantic': semantic_score,
                'signals': signal_bonus,
                'platform': platform_bonus,
                'total': total_score
            }
            
            # Format for frontend
            candidate['name'] = candidate['username'].replace('_', ' ').title()
            candidate['subs'] = self._estimate_followers(candidate)
            candidate['avatar'] = None
            candidate['tags'] = self._infer_tags(candidate, user_hashtags)
            candidate['confidence_score'] = total_score * 100
            candidate['match_reason'] = self._generate_match_reason(candidate)
            candidate['creator_id'] = candidate['username']
            
            scored_candidates.append(candidate)
        
        # Sort by total score
        scored_candidates.sort(key=lambda x: x['scores']['total'], reverse=True)
        
        return scored_candidates
    
    def _estimate_followers(self, candidate: Dict[str, Any]) -> str:
        """
        Estimate follower range from signals.
        Not scraping - inferring from discovery method.
        """
        # If found via Google Trends = likely bigger
        if candidate.get('discovered_via') == 'google_trends':
            return "100K - 500K"
        
        # If found via Reddit = likely medium
        elif candidate.get('discovered_via') == 'reddit':
            return "50K - 200K"
        
        # Default estimate
        return "10K - 100K"
    
    def _infer_tags(self, candidate: Dict[str, Any], user_hashtags: List[str]) -> List[str]:
        """Infer content tags from candidate data"""
        tags = []
        
        # Add content type as tag
        if candidate.get('content_type'):
            tags.append(candidate['content_type'].split()[0])
        
        # Add platform
        if candidate.get('platform'):
            tags.append(candidate['platform'])
        
        # Add matched hashtags
        for hashtag in user_hashtags[:2]:
            clean_tag = hashtag.replace('#', '')
            if clean_tag not in tags:
                tags.append(clean_tag)
        
        return tags[:3]  # Max 3 tags
    
    def _generate_match_reason(self, candidate: Dict[str, Any]) -> str:
        """Generate human-readable match reason"""
        score = candidate['scores']['total']
        signals = candidate.get('discovery_signals', 1)
        
        if signals > 2:
            return "Found via multiple sources"
        elif score > 0.8:
            return "Highly similar content"
        elif candidate.get('discovered_via') == 'google_trends':
            return "Trending in your niche"
        else:
            return "Similar content style"


def get_semantic_discovery(embedding_service, db=None):
    """Get semantic discovery instance"""
    return SemanticCompetitorDiscovery(embedding_service, db)
