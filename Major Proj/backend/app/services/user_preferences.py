"""
User Preferences Service - ML Enhanced
Advanced learning system using vector embeddings and feedback
"""
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """
    ML-enhanced preference learning using vector embeddings.
    Implements Spotify-style recommendation learning.
    """
    
    def __init__(self):
        # Store user embeddings (not just tag weights)
        self.user_data = defaultdict(lambda: {
            'embedding': None,  # User's content vector
            'selected_ids': set(),
            'rejected_ids': set(),
            'selected_embeddings': [],  # Store embeddings of selected creators
            'rejected_embeddings': [],  # Store embeddings of rejected creators
            'interaction_history': []
        })
    
    def track_selection(
        self, 
        user_id: str, 
        creator_id: str, 
        creator_embedding: np.ndarray,
        creator_tags: List[str] = None
    ):
        """
        Track when a user selects a creator.
        Pulls user vector toward selected creator (Spotify approach).
        
        Args:
            user_id: User ID
            creator_id: Selected creator ID
            creator_embedding: Creator's embedding vector
            creator_tags: Creator tags (for logging)
        """
        user_prefs = self.user_data[user_id]
        user_prefs['selected_ids'].add(creator_id)
        user_prefs['selected_embeddings'].append(creator_embedding)
        
        # Update user embedding using weighted average
        if user_prefs['embedding'] is None:
            # First selection: initialize with creator embedding
            user_prefs['embedding'] = creator_embedding.copy()
        else:
            # Pull user vector toward selected creator
            # Formula: user_vec = 0.7 * user_vec + 0.3 * creator_vec
            alpha = 0.3  # Learning rate
            user_prefs['embedding'] = (
                (1 - alpha) * user_prefs['embedding'] + 
                alpha * creator_embedding
            )
        
        # Record interaction
        user_prefs['interaction_history'].append({
            'action': 'selected',
            'creator_id': creator_id,
            'tags': creator_tags or [],
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"User {user_id} selected creator {creator_id}. Vector updated.")
    
    def track_rejection(
        self, 
        user_id: str, 
        creator_id: str, 
        creator_embedding: np.ndarray,
        creator_tags: List[str] = None,
        reason: Optional[str] = None
    ):
        """
        Track when a user rejects a creator.
        Pushes user vector away from rejected creator (Spotify approach).
        
        Args:
            user_id: User ID
            creator_id: Rejected creator ID
            creator_embedding: Creator's embedding vector
            creator_tags: Creator tags (for logging)
            reason: Optional rejection reason
        """
        user_prefs = self.user_data[user_id]
        user_prefs['rejected_ids'].add(creator_id)
        user_prefs['rejected_embeddings'].append(creator_embedding)
        
        # Update user embedding by pushing away
        if user_prefs['embedding'] is not None:
            # Formula: user_vec = user_vec - α * (creator_vec - user_vec)
            # This moves user away from rejected region
            alpha = 0.2  # Smaller learning rate for rejections
            diff = creator_embedding - user_prefs['embedding']
            user_prefs['embedding'] = user_prefs['embedding'] - alpha * diff
        
        # Record interaction
        user_prefs['interaction_history'].append({
            'action': 'rejected',
            'creator_id': creator_id,
            'tags': creator_tags or [],
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"User {user_id} rejected creator {creator_id}. Vector pushed away.")
    
    def get_user_embedding(self, user_id: str) -> Optional[np.ndarray]:
        """
        Get current user embedding vector.
        
        Returns:
            User's content vector or None if no interactions yet
        """
        return self.user_data[user_id].get('embedding')
    
    def set_user_embedding(self, user_id: str, embedding: np.ndarray):
        """
        Set initial user embedding (from profile analysis).
        
        Args:
            user_id: User ID
            embedding: Initial embedding vector
        """
        self.user_data[user_id]['embedding'] = embedding.copy()
        logger.info(f"Set initial embedding for user {user_id}")
    
    def get_selected_cluster_centroid(self, user_id: str) -> Optional[np.ndarray]:
        """
        Calculate centroid of selected creators.
        Used for "More Like This" recommendations.
        
        Returns:
            Mean of selected creator embeddings
        """
        selected_embeddings = self.user_data[user_id].get('selected_embeddings', [])
        
        if not selected_embeddings:
            return None
        
        # Return mean of selected embeddings
        return np.mean(selected_embeddings, axis=0)
    
    def get_rejected_cluster_centroid(self, user_id: str) -> Optional[np.ndarray]:
        """
        Calculate centroid of rejected creators.
        Used to avoid similar suggestions.
        
        Returns:
            Mean of rejected creator embeddings
        """
        rejected_embeddings = self.user_data[user_id].get('rejected_embeddings', [])
        
        if not rejected_embeddings:
            return None
        
        return np.mean(rejected_embeddings, axis=0)
    
    def is_creator_rejected(self, user_id: str, creator_id: str) -> bool:
        """Check if creator was rejected by user"""
        return creator_id in self.user_data[user_id]['rejected_ids']
    
    def is_creator_selected(self, user_id: str, creator_id: str) -> bool:
        """Check if creator was selected by user"""
        return creator_id in self.user_data[user_id]['selected_ids']
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user preferences.
        """
        user_prefs = self.user_data[user_id]
        
        return {
            'total_selections': len(user_prefs['selected_ids']),
            'total_rejections': len(user_prefs['rejected_ids']),
            'has_embedding': user_prefs['embedding'] is not None,
            'interaction_count': len(user_prefs['interaction_history'])
        }
    
    def reset_user_preferences(self, user_id: str):
        """
        Reset all preferences for a user.
        """
        if user_id in self.user_data:
            del self.user_data[user_id]
            logger.info(f"Reset preferences for user {user_id}")


# Global instance
user_preferences_service = UserPreferencesService()
