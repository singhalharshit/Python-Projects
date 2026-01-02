"""
Decision Assistant - Main orchestrator for the entire system
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from app.services.signals.abstract_signal import DailyDecision, CreatorEmbedding
from app.services.signals.live_signal_collector import LiveSignalCollector
from app.services.intelligence.vector_store import get_vector_store
from app.services.intelligence.niche_discovery import NicheDiscoveryEngine
from app.services.intelligence.competitor_discovery import CompetitorDiscoveryEngine
from app.services.intelligence.preference_learner import PreferenceLearner
from app.services.intelligence.emotional_tracker import EmotionalStateTracker
from app.services.intelligence.opportunity_detector import OpportunityDetector
from app.services.intelligence.decision_synthesizer import DecisionSynthesizer
from app.services.intelligence.embedding_service import EmbeddingService
from app.services.intelligence.emotional_safety_system import EmotionalSafetySystem

logger = logging.getLogger(__name__)


class DecisionAssistant:
    """
    Main orchestrator for the emotionally intelligent decision assistant.
    
    This is the entry point for all major operations:
    - Onboarding new creators
    - Generating daily decisions
    - Recording user actions
    - Learning from behavior
    
    Philosophy:
    - Emotional safety first
    - Learn from behavior, not questions
    - ONE calm decision per day
    - Rest is productive
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize core services
        self.vector_store = get_vector_store()
        self.embedding_service = EmbeddingService()
        
        # Initialize intelligence layers
        self.niche_discovery = NicheDiscoveryEngine(db)
        self.competitor_discovery = CompetitorDiscoveryEngine(
            vector_store=self.vector_store,
            db=db
        )
        self.preference_learner = PreferenceLearner(db)
        self.emotional_tracker = EmotionalStateTracker(db)
        
        # Initialize signal collection
        self.signal_collector = LiveSignalCollector(db)
        
        # Initialize opportunity detection
        self.opportunity_detector = OpportunityDetector(
            signal_collector=self.signal_collector,
            competitor_engine=self.competitor_discovery
        )
        
        # Initialize decision synthesis
        self.decision_synthesizer = DecisionSynthesizer(
            emotional_tracker=self.emotional_tracker,
            preference_learner=self.preference_learner,
            opportunity_detector=self.opportunity_detector
        )
        
        logger.info("DecisionAssistant initialized")
    
    async def onboard_creator(
        self,
        user_id: str,
        profile_data: dict,
        content_samples: List[str] = None
    ) -> dict:
        """
        Onboard a new creator.
        
        Steps:
        1. Analyze profile and content
        2. Generate multi-dimensional embedding
        3. Store in vector store
        4. Discover niche
        5. Find competitors
        6. Initialize preferences
        7. Initialize emotional state
        
        Args:
            user_id: Unique user ID
            profile_data: Profile information (bio, platform, etc.)
            content_samples: Recent posts/content
        
        Returns:
            Onboarding result dict
        """
        logger.info(f"Onboarding creator {user_id}")
        
        # 1. Generate creator embedding
        creator_embedding = await self._analyze_creator_profile(
            user_id,
            profile_data,
            content_samples or []
        )
        
        # 2. Store in vector store
        self.vector_store.add_creator(
            creator_id=user_id,
            embedding=creator_embedding.theme,  # Store theme vector
            metadata={
                'platform': profile_data.get('platform', 'unknown'),
                'bio': profile_data.get('bio', ''),
                'follower_count': profile_data.get('follower_count', 0),
                'onboarded_at': datetime.utcnow().isoformat()
            }
        )
        
        # 3. Discover niche
        niche = self.niche_discovery.discover_niche_for_creator(creator_embedding)
        
        # 4. Find competitors
        competitors = self.competitor_discovery.discover_competitors(
            creator_embedding=creator_embedding,
            k=50
        )
        
        # 5. Initialize preferences (use creator's own content as starting point)
        self.preference_learner.initialize_user(
            user_id=user_id,
            initial_vector=creator_embedding.theme
        )
        
        # 6. Initialize emotional state
        self.emotional_tracker.get_or_create_state(user_id)
        
        logger.info(
            f"Onboarded {user_id}: "
            f"niche={niche.label if niche else 'unknown'}, "
            f"competitors={len(competitors)}"
        )
        
        return {
            'user_id': user_id,
            'niche': niche.to_dict() if niche else None,
            'competitors': [c.to_dict() for c in competitors[:10]],
            'onboarded_at': datetime.utcnow().isoformat()
        }
    
    async def get_daily_decision(self, user_id: str) -> DailyDecision:
        """
        Generate ONE calm daily decision for a creator.
        
        This is the main entry point for daily recommendations.
        
        Args:
            user_id: User ID
        
        Returns:
            DailyDecision
        """
        logger.info(f"Generating daily decision for {user_id}")
        
        # ✅ STEP 1: Check safety gates FIRST (emotional safety is non-negotiable)
        safety_system = EmotionalSafetySystem(
            db=self.db,
            emotional_tracker=self.emotional_tracker
        )
        
        safety_check = safety_system.check_safety_gates(
            user_id=user_id,
            proposed_action='post'
        )
        
        # ✅ STEP 2: If not safe, return override decision immediately
        if not safety_check['safe']:
            logger.info(
                f"Safety override for {user_id}: "
                f"{safety_check['override_action']} "
                f"(severity: {safety_check['severity']})"
            )
            
            return self._create_safety_override_decision(
                user_id=user_id,
                safety_check=safety_check
            )
        
        # ✅ STEP 3: Log warnings if present (but proceed with caution)
        if safety_check['gates_triggered']:
            logger.warning(
                f"Safety warnings for {user_id}: "
                f"{[g.rule_name for g in safety_check['gates_triggered']]}"
            )
        
        # 1. Get creator embedding from vector store
        creator_data = self.vector_store.get_creator_embedding(user_id)
        
        if creator_data is None:
            logger.error(f"Creator {user_id} not found in vector store")
            raise ValueError(f"Creator {user_id} not onboarded")
        
        # Reconstruct CreatorEmbedding
        creator_embedding = CreatorEmbedding(
            theme=creator_data,
            tone=np.zeros(5),  # Would be stored separately in production
            format=np.zeros(4),
            trajectory=np.zeros(4),
            creator_id=user_id,
            platform='unknown',  # Would be from metadata
            analyzed_at=datetime.utcnow(),
            post_count=0
        )
        
        # 2. Get competitors
        competitors = self.competitor_discovery.discover_competitors(
            creator_embedding=creator_embedding,
            k=20
        )
        
        # 3. Synthesize decision
        decision = self.decision_synthesizer.synthesize_daily_decision(
            user_id=user_id,
            creator_embedding=creator_embedding,
            competitors=competitors
        )
        
        logger.info(
            f"Generated decision for {user_id}: "
            f"action={decision.action}, "
            f"topic={decision.topic}, "
            f"confidence={decision.confidence:.2f}"
        )
        
        return decision
    
    async def record_action(
        self,
        user_id: str,
        action_type: str,
        content_vector: Optional[np.ndarray] = None,
        context: dict = None
    ):
        """
        Record a user action for learning.
        
        Actions: select, reject, ignore, follow, rest
        
        Args:
            user_id: User ID
            action_type: Type of action
            content_vector: Content vector (if applicable)
            context: Optional context metadata
        """
        logger.info(f"Recording {action_type} action for {user_id}")
        
        # 1. Update preferences (if content-related action)
        if content_vector is not None and action_type in ['select', 'reject', 'ignore', 'follow']:
            self.preference_learner.update_from_action(
                user_id=user_id,
                action_type=action_type,
                content_vector=content_vector,
                context=context
            )
        
        # 2. Update emotional state
        self.emotional_tracker.update_from_action(
            user_id=user_id,
            action_type=action_type,
            context=context
        )
        
        logger.info(f"Action recorded for {user_id}")
    
    async def _analyze_creator_profile(
        self,
        user_id: str,
        profile_data: dict,
        content_samples: List[str]
    ) -> CreatorEmbedding:
        """
        Analyze creator profile and generate multi-dimensional embedding.
        
        Args:
            user_id: User ID
            profile_data: Profile data
            content_samples: Content samples
        
        Returns:
            CreatorEmbedding
        """
        # Combine bio and content for analysis
        bio = profile_data.get('bio')
        if bio is None:
            bio = ""
            
        all_text = [bio] + (content_samples or [])
        combined_text = " ".join([t for t in all_text if t])  # Filter out empty strings/None safely
        
        # Generate theme embedding
        theme_vector = self.embedding_service.encode_text(combined_text)
        
        # For now, use simplified tone/format/trajectory
        # In production, these would be extracted from content analysis
        tone_vector = np.zeros(5)
        format_vector = np.zeros(4)
        trajectory_vector = np.zeros(4)
        
        return CreatorEmbedding(
            theme=theme_vector,
            tone=tone_vector,
            format=format_vector,
            trajectory=trajectory_vector,
            creator_id=user_id,
            platform=profile_data.get('platform', 'unknown'),
            analyzed_at=datetime.utcnow(),
            post_count=len(content_samples)
        )
    
    def _create_safety_override_decision(
        self,
        user_id: str,
        safety_check: dict
    ) -> DailyDecision:
        """
        Create a decision that overrides normal synthesis for safety.
        
        This is called when safety gates detect creator wellbeing issues.
        The system prioritizes emotional safety over content opportunities.
        
        Args:
            user_id: User ID
            safety_check: Safety check result from EmotionalSafetySystem
        
        Returns:
            DailyDecision with safety override
        """
        action = safety_check['override_action']  # 'rest' or 'observe'
        
        # Get emotional context
        emotional_context = self.emotional_tracker.get_emotional_context(user_id)
        
        # Build metadata with safety gate details
        metadata = {
            'safety_override': True,
            'severity': safety_check['severity'],
            'gates_triggered': [
                {
                    'rule': gate.rule_name,
                    'severity': gate.severity,
                    'explanation': gate.explanation,
                    'recommended_action': gate.recommended_action
                }
                for gate in safety_check['gates_triggered']
            ],
            'override_timestamp': datetime.utcnow().isoformat()
        }
        
        # Create appropriate decision based on override action
        if action == 'rest':
            return DailyDecision(
                action='rest',
                topic=None,
                confidence=1.0,  # High confidence in safety decision
                explanation=safety_check['explanation'],
                timing=None,
                alternatives=[],
                avoid=[],
                emotional_context={
                    'tone': 'protective',
                    'reassurance': 'Your wellbeing comes first',
                    'state': emotional_context.get('overall_state', 'neutral')
                },
                metadata=metadata
            )
        else:  # observe
            return DailyDecision(
                action='observe',
                topic=None,
                confidence=0.8,
                explanation=safety_check['explanation'],
                timing=None,
                alternatives=[],
                avoid=[],
                emotional_context={
                    'tone': 'cautious',
                    'reassurance': 'Sometimes the best move is to watch and wait',
                    'state': emotional_context.get('overall_state', 'neutral')
                },
                metadata=metadata
            )
    
    def get_user_stats(self, user_id: str) -> dict:
        """
        Get comprehensive stats for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Stats dict
        """
        # Get emotional state
        emotional_state = self.emotional_tracker.get_state_summary(user_id)
        
        # Get action statistics
        action_stats = self.preference_learner.get_action_statistics(user_id)
        
        # Get rest patterns
        rest_patterns = self.preference_learner.infer_rest_patterns(user_id)
        
        # Get preference stability
        stability = self.preference_learner.get_preference_stability(user_id)
        
        return {
            'user_id': user_id,
            'emotional_state': emotional_state,
            'action_stats': action_stats,
            'rest_patterns': rest_patterns,
            'preference_stability': stability
        }
