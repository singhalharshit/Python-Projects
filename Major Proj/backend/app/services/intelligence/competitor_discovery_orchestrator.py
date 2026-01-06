"""
Competitor Discovery Orchestrator
Main service that coordinates candidate generation, scoring, and learning

This is the primary entry point for competitor discovery.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.competitor_candidate import CompetitorCandidate
from app.services.intelligence.candidate_generator import CandidateGenerator
from app.services.intelligence.competitor_scorer import CompetitorScorer
from app.services.intelligence.competitor_preference_learner import CompetitorPreferenceLearner

logger = logging.getLogger(__name__)


class CompetitorDiscoveryOrchestrator:
    """
    Orchestrates the entire competitor discovery process.
    
    Flow:
    1. Generate candidates (50-200 raw candidates)
    2. Score candidates (multi-signal weighted scoring)
    3. Rank and filter (top N)
    4. Store candidates for tracking
    5. Return top suggestions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.candidate_generator = CandidateGenerator(db)
        self.scorer = CompetitorScorer(db)
        self.learner = CompetitorPreferenceLearner(db)
    
    async def discover_competitors(
        self,
        user_id: str,
        username: str,
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Discover competitors for a user.
        """
        logger.info(f"Starting competitor discovery for {username}")
        
        try:
            # Step 1: Generate candidates
            candidate_usernames = await self.candidate_generator.generate_candidates(
                user_id=user_id,
                username=username,
                target_count=100
            )
            
            if not candidate_usernames:
                logger.warning(f"No candidates generated for {username}")
                return self._generate_low_confidence_response()
            
            logger.info(f"Generated {len(candidate_usernames)} candidates")
            
            # Step 2: Score candidates
            scored_candidates = self.scorer.score_candidates(
                user_id=user_id,
                user_username=username,
                candidate_usernames=candidate_usernames
            )
            
            if not scored_candidates:
                logger.warning(f"No candidates scored for {username}")
                return self._generate_low_confidence_response()
            
            logger.info(f"Scored {len(scored_candidates)} candidates")
            
            # Step 3: Take top N
            top_candidates = scored_candidates[:limit]
            
            # Step 4: Store candidates in database
            self._store_candidates(user_id, top_candidates)
            
            # Step 5: Format response
            response = self._format_response(top_candidates)
            
            logger.info(f"Returning {len(response)} competitors for {username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to discover competitors for {username}: {e}")
            self.db.rollback()  # ✅ FIX: Ensure session is clean for subsequent requests
            return self._generate_error_response(str(e))
    
    def handle_feedback(
        self,
        user_id: str,
        creator_id: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Handle user feedback (accept/reject) and update preferences.
        
        Args:
            user_id: User's ID
            creator_id: Competitor creator ID
            action: 'accept' or 'reject'
        
        Returns:
            Status and updated weights
        """
        logger.info(f"Handling {action} feedback for user {user_id}")
        
        try:
            # Get the candidate record to retrieve signals
            candidate = self.db.query(CompetitorCandidate).filter(
                CompetitorCandidate.user_id == user_id,
                CompetitorCandidate.creator_id == creator_id
            ).first()
            
            if not candidate:
                logger.warning(f"Candidate not found: {creator_id}")
                # Still update with empty signals
                signals = {}
                confidence = 0.5
            else:
                signals = candidate.signals_json or {}
                confidence = candidate.total_score
            
            # Update preferences
            self.learner.update_from_feedback(
                user_id=user_id,
                creator_id=creator_id,
                action=action,
                signals=signals,
                confidence=confidence
            )
            
            # Get updated weights
            updated_weights = self.learner.get_user_weights(user_id)
            
            return {
                'status': 'success',
                'action': action,
                'updated_weights': updated_weights
            }
            
        except Exception as e:
            logger.error(f"Failed to handle feedback: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_user_weights(self, user_id: str) -> Dict[str, float]:
        """Get user's learned weights"""
        return self.learner.get_user_weights(user_id)
    
    def _store_candidates(self, user_id: str, candidates: List[Dict]):
        """Store candidates in database for tracking"""
        try:
            for candidate in candidates:
                db_candidate = CompetitorCandidate(
                    user_id=user_id,
                    creator_id=candidate['creator_id'] or candidate['username'],
                    total_score=candidate['total_score'],
                    rank=candidate['rank'],
                    signals_json=candidate['signals'],
                    discovery_path='multi',  # Multiple paths used
                    shown_to_user=True,
                    shown_at=datetime.now()
                )
                self.db.add(db_candidate)
            
            self.db.commit()
            logger.info(f"Stored {len(candidates)} candidates in database")
            
        except Exception as e:
            logger.error(f"Failed to store candidates: {e}")
            self.db.rollback()
    
    def _format_response(self, candidates: List[Dict]) -> List[Dict[str, Any]]:
        """Format candidates for API response"""
        formatted = []
        
        for candidate in candidates:
            profile = candidate.get('profile', {})
            full_name = profile.get('full_name') or ""
            username = candidate['username']
            
            # 1. Format follower count (frontend expects 'subs' string)
            followers = profile.get('follower_count', 0)
            subs = self._format_number(followers)
            
            item = {
                'id': candidate.get('creator_id') or username, # Frontend uses 'id'
                'username': username,
                'creator_id': candidate.get('creator_id'),
                'rank': candidate['rank'],
                'score': round(candidate['total_score'], 3),
                'signals': {
                    k: round(v, 3) if v is not None else None
                    for k, v in candidate['signals'].items()
                },
                'profile': profile,
                'match_reason': self._generate_match_reason(candidate),
                
                # ✅ Frontend Compatibility Fields
                'name': full_name if full_name.strip() else username,
                'avatar': profile.get('profile_pic_url'),
                'subs': subs,
                'tags': profile.get('keywords', []) # Frontend tracks 'tags'
            }
            formatted.append(item)
        
        return formatted

    def _format_number(self, num: int) -> str:
        """Format number to K/M string (e.g., 1500 -> 1.5K)"""
        if not num: return "0"
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num/1_000:.1f}K"
        return str(num)

    def _generate_match_reason(self, candidate: Dict) -> str:
        """Generate human-readable match reason"""
        signals = candidate['signals']
        
        # Find strongest signal
        valid_signals = {k: v for k, v in signals.items() if v is not None and v > 0.5}
        
        if not valid_signals:
            return "Similar content style"
        
        strongest = max(valid_signals.items(), key=lambda x: x[1])
        signal_name, signal_value = strongest
        
        reasons = {
            'content_similarity': "Similar content themes and style",
            'hashtag_overlap': "Uses similar hashtags",
            'audio_overlap': "Uses similar audio/music",
            'engagement_similarity': "Similar engagement patterns",
            'tier_similarity': "Similar audience size",
            'time_similarity': "Posts at similar times"
        }
        
        return reasons.get(signal_name, "Similar creator profile")
    
    def _generate_low_confidence_response(self) -> List[Dict]:
        """Generate response when confidence is low"""
        return [{
            'message': "We're still learning your space. These are early suggestions.",
            'confidence': 'low',
            'suggestions': []
        }]
    
    def _generate_error_response(self, error: str) -> List[Dict]:
        """Generate error response"""
        return [{
            'message': f"Unable to generate suggestions: {error}",
            'confidence': 'error',
            'suggestions': []
        }]
