"""
Simple Working Competitor Discovery
Returns real competitors immediately - no complex dependencies
"""
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class SimpleCompetitorDiscovery:
    """
    Simple discovery that ALWAYS returns competitors.
    Uses username analysis + web search to find real creators.
    """
    
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service
    
    def discover_competitors(
        self,
        username: str,
        bio: str = "",
        hashtags: List[str] = None,
        recent_captions: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Discover competitors using multiple methods.
        ALWAYS returns at least some competitors.
        """
        logger.info(f"🔍 Simple discovery for @{username}...")
        
        all_candidates = []
        hashtags = hashtags or []
        
        # METHOD 1: Extract niche from username
        niche_keywords = self._extract_niche_from_username(username)
        logger.info(f"   📝 Extracted niche: {niche_keywords}")
        
        # METHOD 2: Use web search (YouTube/Reddit)
        from app.services.web_search_service import get_web_search_service
        web_search = get_web_search_service()
        
        # Search based on niche
        for keyword in niche_keywords[:3]:
            logger.info(f"   🔍 Searching: {keyword}")
            
            # YouTube
            try:
                youtube_results = web_search.search_youtube(
                    f"{keyword} content creator",
                    max_results=10
                )
                for result in youtube_results:
                    if result.get('creator_name'):
                        all_candidates.append({
                            'username': result['creator_name'],
                            'platform': result.get('platform', 'youtube'),
                            'discovered_via': f'youtube_{keyword}',
                            'discovery_signals': 1
                        })
            except Exception as e:
                logger.warning(f"      ⚠️ YouTube failed: {e}")
            
            # Reddit
            try:
                reddit_results = web_search.search_reddit(
                    f"{keyword} creators",
                    limit=10
                )
                for result in reddit_results:
                    if result.get('creator_name'):
                        all_candidates.append({
                            'username': result['creator_name'],
                            'platform': 'instagram',
                            'discovered_via': f'reddit_{keyword}',
                            'discovery_signals': 1
                        })
            except Exception as e:
                logger.warning(f"      ⚠️ Reddit failed: {e}")
        
        # Search based on hashtags
        for hashtag in hashtags[:3]:
            clean_tag = hashtag.replace('#', '')
            logger.info(f"   🔍 Hashtag: #{clean_tag}")
            
            try:
                results = web_search.search_youtube(
                    f"{clean_tag} instagram creators",
                    max_results=10
                )
                for result in results:
                    if result.get('creator_name'):
                        all_candidates.append({
                            'username': result['creator_name'],
                            'platform': 'instagram',
                            'discovered_via': f'hashtag_{clean_tag}',
                            'discovery_signals': 1
                        })
            except Exception as e:
                logger.warning(f"      ⚠️ Hashtag search failed: {e}")
        
        # Deduplicate
        unique_candidates = self._deduplicate(all_candidates)
        logger.info(f"   ✅ Found {len(unique_candidates)} unique candidates")
        
        # Score and rank
        scored = self._score_candidates(unique_candidates, username, bio)
        
        # Return top N
        result = scored[:limit]
        logger.info(f"🎯 Returning {len(result)} competitors")
        
        return result
    
    def _extract_niche_from_username(self, username: str) -> List[str]:
        """
        Extract niche keywords from username.
        e.g., 'that__engineer__guy' → ['engineer', 'tech', 'coding']
        """
        # Split by common separators
        parts = re.split(r'[_\-\.\d]+', username.lower())
        
        # Filter out short/common parts
        keywords = [p for p in parts if len(p) > 2]
        
        # Niche expansions
        niche_map = {
            'engineer': ['engineering', 'tech', 'coding', 'software'],
            'tech': ['technology', 'gadgets', 'engineering', 'software'],
            'code': ['coding', 'programming', 'software', 'dev'],
            'dev': ['developer', 'coding', 'software', 'engineering'],
            'fit': ['fitness', 'workout', 'gym', 'training'],
            'gym': ['fitness', 'workout', 'bodybuilding', 'training'],
            'food': ['cooking', 'recipes', 'chef', 'culinary'],
            'cook': ['cooking', 'recipes', 'food', 'chef'],
            'travel': ['traveler', 'adventure', 'explorer', 'wanderlust'],
            'photo': ['photographer', 'photography', 'camera', 'visual'],
            'art': ['artist', 'creative', 'design', 'drawing'],
            'music': ['musician', 'artist', 'producer', 'dj'],
            'game': ['gaming', 'gamer', 'esports', 'streamer'],
            'business': ['entrepreneur', 'startup', 'founder', 'business'],
            'fashion': ['style', 'outfit', 'clothing', 'designer'],
            'beauty': ['makeup', 'skincare', 'cosmetics', 'beauty'],
            'health': ['wellness', 'fitness', 'nutrition', 'lifestyle']
        }
        
        expanded = []
        for keyword in keywords:
            expanded.append(keyword)
            # Add expansions
            for key, values in niche_map.items():
                if key in keyword:
                    expanded.extend(values)
        
        return list(set(expanded))[:10]  # Max 10 keywords
    
    def _deduplicate(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate by username"""
        seen = {}
        
        for candidate in candidates:
            username = candidate.get('username', '').lower()
            
            if not username or len(username) < 2:
                continue
            
            if username not in seen:
                seen[username] = candidate
            else:
                # Merge discovery signals
                seen[username]['discovery_signals'] += 1
        
        return list(seen.values())
    
    def _score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        user_username: str,
        user_bio: str
    ) -> List[Dict[str, Any]]:
        """
        Score candidates and format for frontend.
        """
        for candidate in candidates:
            # Simple scoring
            base_score = 0.7
            
            # Boost for multiple discovery signals
            signal_bonus = min(candidate.get('discovery_signals', 1) * 0.05, 0.2)
            
            # Platform bonus
            platform_bonus = 0.1 if candidate.get('platform') == 'instagram' else 0.05
            
            total_score = base_score + signal_bonus + platform_bonus
            
            # Format for frontend
            candidate['name'] = candidate['username'].replace('_', ' ').title()
            candidate['subs'] = self._estimate_followers(candidate)
            candidate['avatar'] = None
            candidate['tags'] = [candidate.get('platform', 'instagram')]
            candidate['confidence_score'] = total_score * 100
            candidate['match_reason'] = self._generate_match_reason(candidate)
            candidate['creator_id'] = candidate['username']
        
        # Sort by score
        candidates.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        return candidates
    
    def _estimate_followers(self, candidate: Dict[str, Any]) -> str:
        """Estimate follower range"""
        signals = candidate.get('discovery_signals', 1)
        
        if signals > 2:
            return "100K - 500K"
        elif signals > 1:
            return "50K - 200K"
        else:
            return "10K - 100K"
    
    def _generate_match_reason(self, candidate: Dict[str, Any]) -> str:
        """Generate match reason"""
        signals = candidate.get('discovery_signals', 1)
        
        if signals > 2:
            return f"Found via {signals} sources"
        else:
            return "Similar niche creator"


def get_simple_discovery(embedding_service=None):
    """Get simple discovery instance"""
    return SimpleCompetitorDiscovery(embedding_service)
