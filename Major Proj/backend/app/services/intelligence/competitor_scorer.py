"""
Competitor Scorer
Computes competitor scores using weighted multi-signal formula

Formula:
score = w1*content + w2*hashtag + w3*audio + w4*engagement + w5*tier + w6*time

Signals:
1. Content Similarity (bio + captions)
2. Hashtag Overlap
3. Audio Overlap
4. Engagement Pattern Similarity
5. Follower Tier Similarity
6. Posting Time Similarity
"""
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
from collections import Counter

from app.models.creator import Creator
from app.models.creator_post import CreatorPost
from app.models.user_preference_weights import UserPreferenceWeights
from app.services.scrapers.hybrid_instagram_scraper import get_hybrid_instagram_scraper

logger = logging.getLogger(__name__)


class CompetitorScorer:
    """
    Scores competitor candidates using multi-signal analysis.
    
    Features:
    - Learnable weights (personalized per user)
    - Graceful degradation (missing signals)
    - Explainable scores (signal breakdown)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scraper = get_hybrid_instagram_scraper()
    
    def score_candidates(
        self,
        user_id: str,
        user_username: str,
        candidate_usernames: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Score all candidates for a user.
        
        Args:
            user_id: User's ID (UUID)
            user_username: User's Instagram username
            candidate_usernames: List of candidate usernames
        
        Returns:
            List of scored candidates with signal breakdowns
        """
        logger.info(f"Scoring {len(candidate_usernames)} candidates for {user_username}")
        
        # Get user's preference weights
        weights = self._get_user_weights(user_id)
        
        # Get user's data
        user_profile = self.scraper.get_profile(user_username)
        user_posts = self.scraper.get_recent_posts(user_username, limit=30)
        
        if not user_profile:
            logger.error(f"Could not get profile for {user_username}")
            return []
        
        # Score each candidate
        scored_candidates = []
        
        for candidate_username in candidate_usernames:
            try:
                score_data = self._score_single_candidate(
                    user_profile=user_profile,
                    user_posts=user_posts,
                    candidate_username=candidate_username,
                    weights=weights
                )
                
                if score_data:
                    scored_candidates.append(score_data)
                    
            except Exception as e:
                logger.error(f"Failed to score {candidate_username}: {e}")
                continue
        
        # Sort by total score
        scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add ranks
        for i, candidate in enumerate(scored_candidates):
            candidate['rank'] = i + 1
        
        logger.info(f"Successfully scored {len(scored_candidates)} candidates")
        
        return scored_candidates
    
    def _get_user_weights(self, user_id: str) -> Dict[str, float]:
        """Get user's learned weights or defaults"""
        try:
            weights_record = self.db.query(UserPreferenceWeights).filter(
                UserPreferenceWeights.user_id == user_id
            ).first()
        except Exception as e:
            logger.warning(f"Could not fetch user weights (using defaults): {e}")
            self.db.rollback() # Ensure session is clean
            weights_record = None
        
        if weights_record:
            return {
                'content': weights_record.content_weight,
                'hashtag': weights_record.hashtag_weight,
                'audio': weights_record.audio_weight,
                'engagement': weights_record.engagement_weight,
                'tier': weights_record.tier_weight,
                'time': weights_record.time_weight
            }
        else:
            # Default weights
            return {
                'content': 0.20,
                'hashtag': 0.20,
                'audio': 0.15,
                'engagement': 0.15,
                'tier': 0.15,
                'time': 0.15
            }
    
    def _score_single_candidate(
        self,
        user_profile: Dict,
        user_posts: List[Dict],
        candidate_username: str,
        weights: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Score a single candidate"""
        
        # Get candidate data
        candidate_profile = self.scraper.get_profile(candidate_username)
        
        if not candidate_profile:
            return None
        
        # Skip private accounts
        if candidate_profile.get('is_private', False):
            logger.debug(f"Skipping private account: {candidate_username}")
            return None
        
        candidate_posts = self.scraper.get_recent_posts(candidate_username, limit=30)
        
        # Compute individual signals
        signals = {}
        
        # 1. Content Similarity
        signals['content_similarity'] = self._compute_content_similarity(
            user_profile, user_posts, candidate_profile, candidate_posts
        )
        
        # 2. Hashtag Overlap
        signals['hashtag_overlap'] = self._compute_hashtag_overlap(
            user_posts, candidate_posts
        )
        
        # 3. Audio Overlap (limited for public API)
        signals['audio_overlap'] = self._compute_audio_overlap(
            user_posts, candidate_posts
        )
        
        # 4. Engagement Pattern Similarity
        signals['engagement_similarity'] = self._compute_engagement_similarity(
            user_profile, user_posts, candidate_profile, candidate_posts
        )
        
        # 5. Follower Tier Similarity
        signals['tier_similarity'] = self._compute_tier_similarity(
            user_profile, candidate_profile
        )
        
        # 6. Posting Time Similarity
        signals['time_similarity'] = self._compute_time_similarity(
            user_posts, candidate_posts
        )
        
        # Compute weighted total score
        total_score = 0.0
        active_weights = 0.0
        
        for signal_name, signal_value in signals.items():
            weight_key = signal_name.replace('_similarity', '').replace('_overlap', '')
            weight = weights.get(weight_key, 0.0)
            
            if signal_value is not None:
                total_score += weight * signal_value
                active_weights += weight
        
        # Normalize by active weights (graceful degradation)
        if active_weights > 0:
            total_score = total_score / active_weights
        
        return {
            'username': candidate_username,
            'creator_id': candidate_profile.get('id'),
            'total_score': total_score,
            'signals': signals,
            'profile': {
                'full_name': candidate_profile.get('full_name') or "",
                'profile_pic_url': candidate_profile.get('profile_pic_url'),
                'bio': candidate_profile.get('bio'),
                'follower_count': candidate_profile.get('follower_count'),
                'verified': candidate_profile.get('verified'),
                'category': candidate_profile.get('category')
            }
        }
    
    def _compute_content_similarity(
        self, user_profile: Dict, user_posts: List[Dict],
        candidate_profile: Dict, candidate_posts: List[Dict]
    ) -> Optional[float]:
        """Compute content similarity (bio + captions)"""
        try:
            user_bio = user_profile.get('bio', '')
            candidate_bio = candidate_profile.get('bio', '')
            
            # Simple word overlap for bio
            user_words = set(user_bio.lower().split())
            candidate_words = set(candidate_bio.lower().split())
            
            if not user_words or not candidate_words:
                return 0.0
            
            bio_similarity = len(user_words & candidate_words) / len(user_words | candidate_words)
            
            # Caption similarity (average)
            user_captions = ' '.join([p.get('caption', '') for p in user_posts])
            candidate_captions = ' '.join([p.get('caption', '') for p in candidate_posts])
            
            user_caption_words = set(user_captions.lower().split())
            candidate_caption_words = set(candidate_captions.lower().split())
            
            if user_caption_words and candidate_caption_words:
                caption_similarity = len(user_caption_words & candidate_caption_words) / len(user_caption_words | candidate_caption_words)
            else:
                caption_similarity = 0.0
            
            # Average of bio and caption similarity
            return (bio_similarity + caption_similarity) / 2.0
            
        except Exception as e:
            logger.error(f"Failed to compute content similarity: {e}")
            return None
    
    def _compute_hashtag_overlap(
        self, user_posts: List[Dict], candidate_posts: List[Dict]
    ) -> Optional[float]:
        """Compute hashtag overlap (Jaccard similarity)"""
        try:
            user_hashtags = set()
            for post in user_posts:
                user_hashtags.update([tag.lower() for tag in post.get('hashtags', [])])
            
            candidate_hashtags = set()
            for post in candidate_posts:
                candidate_hashtags.update([tag.lower() for tag in post.get('hashtags', [])])
            
            if not user_hashtags or not candidate_hashtags:
                return 0.0
            
            # Jaccard similarity
            intersection = len(user_hashtags & candidate_hashtags)
            union = len(user_hashtags | candidate_hashtags)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to compute hashtag overlap: {e}")
            return None
    
    def _compute_audio_overlap(
        self, user_posts: List[Dict], candidate_posts: List[Dict]
    ) -> Optional[float]:
        """Compute audio overlap (limited for public API)"""
        # Audio data not available in public API
        # Return None to trigger graceful degradation
        return None
    
    def _compute_engagement_similarity(
        self, user_profile: Dict, user_posts: List[Dict],
        candidate_profile: Dict, candidate_posts: List[Dict]
    ) -> Optional[float]:
        """Compute engagement pattern similarity"""
        try:
            # Calculate average engagement rates
            user_followers = user_profile.get('follower_count', 1)
            candidate_followers = candidate_profile.get('follower_count', 1)
            
            if user_followers == 0 or candidate_followers == 0:
                return 0.0
            
            # User engagement rate
            user_total_engagement = sum([
                p.get('likes', 0) + p.get('comments', 0) 
                for p in user_posts
            ])
            user_engagement_rate = user_total_engagement / (len(user_posts) * user_followers) if user_posts else 0
            
            # Candidate engagement rate
            candidate_total_engagement = sum([
                p.get('likes', 0) + p.get('comments', 0)
                for p in candidate_posts
            ])
            candidate_engagement_rate = candidate_total_engagement / (len(candidate_posts) * candidate_followers) if candidate_posts else 0
            
            # Similarity using sigmoid of difference
            diff = abs(user_engagement_rate - candidate_engagement_rate)
            similarity = 1.0 / (1.0 + diff * 100)  # Sigmoid-like
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to compute engagement similarity: {e}")
            return None
    
    def _compute_tier_similarity(
        self, user_profile: Dict, candidate_profile: Dict
    ) -> Optional[float]:
        """Compute follower tier similarity"""
        try:
            user_followers = user_profile.get('follower_count', 0)
            candidate_followers = candidate_profile.get('follower_count', 0)
            
            if user_followers == 0 or candidate_followers == 0:
                return 0.0
            
            # Use log scale to compare tiers
            user_log = math.log10(user_followers + 1)
            candidate_log = math.log10(candidate_followers + 1)
            
            # Penalize if too different (>10x difference)
            ratio = max(user_followers, candidate_followers) / min(user_followers, candidate_followers)
            
            if ratio > 10:
                return 0.3  # Low similarity if very different tiers
            
            # Similarity based on log difference
            diff = abs(user_log - candidate_log)
            similarity = 1.0 / (1.0 + diff)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to compute tier similarity: {e}")
            return None
    
    def _compute_time_similarity(
        self, user_posts: List[Dict], candidate_posts: List[Dict]
    ) -> Optional[float]:
        """Compute posting time similarity"""
        try:
            # Extract posting hours
            user_hours = []
            for post in user_posts:
                posted_at = post.get('posted_at')
                if posted_at:
                    try:
                        dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                        user_hours.append(dt.hour)
                    except:
                        continue
            
            candidate_hours = []
            for post in candidate_posts:
                posted_at = post.get('posted_at')
                if posted_at:
                    try:
                        dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                        candidate_hours.append(dt.hour)
                    except:
                        continue
            
            if not user_hours or not candidate_hours:
                return None
            
            # Create hour distributions
            user_dist = Counter(user_hours)
            candidate_dist = Counter(candidate_hours)
            
            # Normalize to probabilities
            user_total = sum(user_dist.values())
            candidate_total = sum(candidate_dist.values())
            
            user_probs = {h: count/user_total for h, count in user_dist.items()}
            candidate_probs = {h: count/candidate_total for h, count in candidate_dist.items()}
            
            # Compute overlap (simplified cosine similarity)
            all_hours = set(user_probs.keys()) | set(candidate_probs.keys())
            
            dot_product = sum([
                user_probs.get(h, 0) * candidate_probs.get(h, 0)
                for h in all_hours
            ])
            
            user_norm = math.sqrt(sum([p**2 for p in user_probs.values()]))
            candidate_norm = math.sqrt(sum([p**2 for p in candidate_probs.values()]))
            
            if user_norm == 0 or candidate_norm == 0:
                return 0.0
            
            similarity = dot_product / (user_norm * candidate_norm)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to compute time similarity: {e}")
            return None
