"""
Competitor Discovery Engine - Automatically find relevant competitors
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np
from sqlalchemy.orm import Session

from app.services.signals.abstract_signal import CreatorEmbedding
from app.services.intelligence.vector_store import VectorStore
from app.services.instagram_scraper import get_instagram_scraper

logger = logging.getLogger(__name__)


@dataclass
class CompetitorProfile:
    """
    Represents a discovered competitor with relevance scoring.
    """
    creator_id: str
    embedding: CreatorEmbedding
    
    # Scoring components
    relevance: float  # Theme similarity (0-1)
    differentiation: float  # How different in tone/format (0-1)
    aspirational_distance: float  # Growth gap (0-1)
    total_score: float  # Combined score
    
    # Metadata
    platform: str
    follower_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """✅ Convert to dictionary with frontend-compatible fields"""
        # Extract metadata if available
        metadata = getattr(self.embedding, 'metadata', {})
        
        return {
            # Backend fields
            'creator_id': self.creator_id,
            'platform': self.platform,
            'scores': {
                'relevance': float(self.relevance),
                'differentiation': float(self.differentiation),
                'aspirational_distance': float(self.aspirational_distance),
                'total': float(self.total_score)
            },
            'follower_count': self.follower_count,
            'engagement_rate': self.engagement_rate,
            
            # ✅ Frontend-compatible fields with metadata
            'name': metadata.get('name', self.creator_id) or self.creator_id,
            'subs': f"{self.follower_count:,}" if self.follower_count else f"{metadata.get('followers', 0):,}" if metadata.get('followers') else 'N/A',
            'avatar': None,  # Will be populated by Instagram scraper
            'tags': [metadata.get('niche', self.platform)] if metadata.get('niche') else [self.platform] if self.platform else [],
            'confidence_score': float(self.total_score * 100),  # Convert to percentage
            'match_reason': self._generate_match_reason()
        }
    
    def _generate_match_reason(self) -> str:
        """Generate human-readable match reason"""
        if self.relevance > 0.8:
            return "Highly relevant content"
        elif self.differentiation > 0.7:
            return "Unique perspective"
        elif self.aspirational_distance > 0.7:
            return "Strong growth trajectory"
        else:
            return "Good overall match"


class CompetitorDiscoveryEngine:
    """
    Discovers competitors purely through content similarity.
    
    Philosophy:
    - NO predefined lists
    - NO manual categorization
    - Pure vector similarity in content space
    - Diversity filtering (not too similar, not too different)
    - Multi-factor ranking
    
    Process:
    1. Find nearest neighbors in theme space
    2. Filter by diversity (0.6-0.9 similarity sweet spot)
    3. Rank by relevance + differentiation + aspiration
    4. Return top competitors
    """
    
    def __init__(self, vector_store: VectorStore, db: Session = None):
        self.vector_store = vector_store
        self.db = db
        self.instagram_scraper = get_instagram_scraper()  # ✅ Add Instagram scraper
    
    def discover_competitors(
        self,
        creator_embedding: CreatorEmbedding,
        k: int = 50,
        diversity_min: float = 0.6,
        diversity_max: float = 0.9
    ) -> List[CompetitorProfile]:
        """
        Discover competitors using vector similarity.
        
        Args:
            creator_embedding: User's content representation
            k: Number of candidates to consider
            diversity_min: Minimum similarity (too different below this)
            diversity_max: Maximum similarity (too similar above this)
        
        Returns:
            Ranked list of CompetitorProfiles
        """
        logger.info(
            f"Discovering competitors for {creator_embedding.creator_id} "
            f"(diversity range: {diversity_min}-{diversity_max})"
        )
        
        # 1. Find nearest neighbors in theme space
        neighbors = self.vector_store.search(
            query_vector=creator_embedding.theme,
            k=k * 2  # Over-fetch for filtering
        )
        
        if not neighbors:
            logger.warning("No neighbors found in vector store")
            return []
        
        # 2. Filter by diversity
        candidates = []
        for neighbor in neighbors:
            # Skip self
            if neighbor['user_id'] == creator_embedding.creator_id:
                continue
            
            neighbor_embedding = neighbor['embedding']
            
            # Calculate theme similarity
            similarity = self._cosine_similarity(
                creator_embedding.theme,
                neighbor_embedding.theme
            )
            
            # Check diversity range
            if diversity_min <= similarity <= diversity_max:
                candidates.append((neighbor, similarity))
        
        logger.info(
            f"Filtered {len(neighbors)} neighbors to {len(candidates)} candidates "
            f"in diversity range"
        )
        
        if not candidates:
            logger.warning("No candidates in strict diversity range. Retrying with wider range...")
            
            # Fallback: Relax diversity constraints completely
            candidates = []
            for neighbor in neighbors:
                # Skip self
                if neighbor['user_id'] == creator_embedding.creator_id:
                    continue
                
                neighbor_embedding = neighbor['embedding']
                
                # Calculate theme similarity
                similarity = self._cosine_similarity(
                    creator_embedding.theme,
                    neighbor_embedding.theme
                )
                
                # Wider range (basically just positive correlation)
                if -1.0 <= similarity <= 1.0: # Allow everything
                    candidates.append((neighbor, similarity))
                    
            logger.info(f"Fallback found {len(candidates)} candidates")

        if not candidates:
            logger.warning("No candidates even with wider range")
            return []
        
        # 3. Rank by multiple factors
        ranked_competitors = self._rank_competitors(
            creator_embedding,
            candidates
        )
        
        # ✅ 4. Enrich top competitors with Instagram data
        top_competitors = ranked_competitors[:20]
        enriched_competitors = self._enrich_with_instagram_data(top_competitors[:5])  # Only enrich top 5 to avoid rate limits
        
        # Combine enriched + non-enriched
        final_competitors = enriched_competitors + top_competitors[5:20]
        
        logger.info(f"Returning {len(final_competitors)} competitors ({len(enriched_competitors)} enriched)")
        
        return final_competitors
    
    def _rank_competitors(
        self,
        creator_embedding: CreatorEmbedding,
        candidates: List[tuple]
    ) -> List[CompetitorProfile]:
        """
        Rank competitors by multiple factors.
        
        Factors:
        - Relevance: Theme similarity (higher = more relevant)
        - Differentiation: Tone/format difference (higher = more unique angle)
        - Aspirational distance: Growth gap (higher = aspirational)
        
        Args:
            creator_embedding: User's embedding
            candidates: List of (neighbor_data, theme_similarity) tuples
        
        Returns:
            Ranked list of CompetitorProfiles
        """
        ranked = []
        
        for neighbor_data, theme_similarity in candidates:
            neighbor_embedding = neighbor_data['embedding']
            
            # Calculate tone difference (want some difference)
            tone_diff = 1 - self._cosine_similarity(
                creator_embedding.tone,
                neighbor_embedding.tone
            )
            
            # Calculate format difference
            format_diff = 1 - self._cosine_similarity(
                creator_embedding.format,
                neighbor_embedding.format
            )
            
            # Differentiation score (average of tone and format differences)
            differentiation_score = (tone_diff + format_diff) / 2
            
            # Calculate aspirational score (are they ahead in growth?)
            # Compare trajectory: recent_avg from neighbor vs user
            user_recent_avg = creator_embedding.trajectory[2] if len(creator_embedding.trajectory) > 2 else 0
            neighbor_recent_avg = neighbor_embedding.trajectory[2] if len(neighbor_embedding.trajectory) > 2 else 0
            
            trajectory_gap = neighbor_recent_avg - user_recent_avg
            aspirational_score = self._sigmoid(trajectory_gap)
            
            # Composite score
            # Weights: relevance 50%, differentiation 30%, aspiration 20%
            total_score = (
                theme_similarity * 0.5 +
                differentiation_score * 0.3 +
                aspirational_score * 0.2
            )
            
            # Create competitor profile
            competitor = CompetitorProfile(
                creator_id=neighbor_data['user_id'],
                embedding=neighbor_embedding,
                relevance=theme_similarity,
                differentiation=differentiation_score,
                aspirational_distance=aspirational_score,
                total_score=total_score,
                platform=neighbor_embedding.platform,
                follower_count=None,  # Would be populated from metadata
                engagement_rate=None
            )
            
            ranked.append(competitor)
        
        # Sort by total score
        ranked.sort(key=lambda x: x.total_score, reverse=True)
        
        return ranked
    
    def _enrich_with_instagram_data(self, competitors: List[CompetitorProfile]) -> List[CompetitorProfile]:
        """
        ✅ Enrich competitor profiles with real Instagram data.
        
        Args:
            competitors: List of competitors from vector similarity
        
        Returns:
            Enriched competitors with real Instagram data
        """
        if not self.instagram_scraper.available:
            logger.warning("Instagram scraper not available, skipping enrichment")
            return competitors
        
        logger.info(f"Enriching {len(competitors)} competitors with Instagram data...")
        
        enriched = []
        for comp in competitors:
            # Try to get Instagram data
            # Assume creator_id is Instagram username
            username = comp.creator_id.replace('instagram_', '')  # Clean prefix if exists
            
            instagram_data = self.instagram_scraper.get_profile(username)
            
            if instagram_data:
                # Update competitor with real data
                comp.follower_count = instagram_data['followers']
                comp.engagement_rate = None  # Would need post data to calculate
                
                logger.info(f"✅ Enriched @{username}: {comp.follower_count:,} followers")
            else:
                logger.debug(f"⚠️  Could not fetch data for {username}")
            
            enriched.append(comp)
        
        return enriched
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid function to normalize scores to 0-1"""
        return float(1 / (1 + np.exp(-x)))
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def get_competitor_gap_analysis(
        self,
        creator_embedding: CreatorEmbedding,
        competitors: List[CompetitorProfile],
        topic_vector: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze if competitors are covering a topic.
        
        Used by OpportunityDetector to find content gaps.
        
        Args:
            creator_embedding: User's embedding
            competitors: List of competitors
            topic_vector: Topic to analyze
        
        Returns:
            Gap analysis dict
        """
        if not competitors:
            return {
                'coverage_ratio': 0.0,
                'gap_score': 1.0,
                'covering_competitors': []
            }
        
        # Check how many competitors are covering this topic
        covering = []
        
        for comp in competitors[:10]:  # Top 10 competitors
            similarity = self._cosine_similarity(
                topic_vector,
                comp.embedding.theme
            )
            
            if similarity > 0.7:  # They're covering it
                covering.append({
                    'creator_id': comp.creator_id,
                    'similarity': float(similarity)
                })
        
        # Calculate coverage ratio
        coverage_ratio = len(covering) / min(len(competitors), 10)
        
        # Gap score (inverse of coverage)
        gap_score = 1 - coverage_ratio
        
        return {
            'coverage_ratio': coverage_ratio,
            'gap_score': gap_score,
            'covering_competitors': covering,
            'total_competitors_checked': min(len(competitors), 10)
        }
