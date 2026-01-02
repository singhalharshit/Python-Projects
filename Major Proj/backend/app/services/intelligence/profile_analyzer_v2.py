"""
Profile Analyzer Service - ML Enhanced
Real ML-based competitor discovery using semantic embeddings
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.intelligence.embedding_service import embedding_service
from app.services.intelligence.vector_store import vector_store
from app.services.intelligence.creator_database import creator_database
from app.services.user_preferences import user_preferences_service

logger = logging.getLogger(__name__)




class ProfileAnalyzer:

    """
    ML-based profile analysis and competitor discovery.
    Uses semantic embeddings and FAISS for similarity search.
    """
    
    def __init__(self):
        # Ensure creator database is loaded
        creator_database.load_creators()
        if not creator_database.is_indexed:
            creator_database.build_index()
        logger.info("ProfileAnalyzer initialized with ML backend")
    
    def analyze_profile(
        self, 
        username: str, 
        user_id: Optional[str] = None,
        bio: str = "",
        recent_content: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze user profile using ML embeddings.
        
        Args:
            username: Username for display
            user_id: User ID for personalization
            bio: User's bio/description
            recent_content: Recent post titles/captions
            
        Returns:
            Analysis with ML-based suggestions
        """
        logger.info(f"Analyzing profile: {username} (ML-based)")
        
        # Generate user embedding from their content
        user_embedding = self._generate_user_embedding(username, bio, recent_content)
        
        # Store initial embedding if user_id provided
        if user_id:
            existing_embedding = user_preferences_service.get_user_embedding(user_id)
            if existing_embedding is None:
                user_preferences_service.set_user_embedding(user_id, user_embedding)
            else:
                # Use learned embedding if exists
                user_embedding = existing_embedding
        
        # Find similar creators using FAISS
        suggestions = self._find_similar_creators(user_embedding, user_id)
        
        # Infer niche from top suggestions
        inferred_niche = self._infer_niche_from_suggestions(suggestions)
        
        return {
            "username": username,
            "inferred_niche": inferred_niche,
            "suggested_competitors": suggestions,
            "ml_powered": True  # Flag to indicate ML backend
        }
    
    def _generate_user_embedding(
        self, 
        username: str, 
        bio: str = "", 
        recent_content: List[str] = None
    ) -> np.ndarray:
        """
        Generate user embedding from available data.
        In production, this would scrape their actual profile.
        For now, we infer from username + provided data.
        """
        # If bio and content provided, use them
        if bio or recent_content:
            return embedding_service.generate_user_vector(
                bio=bio,
                titles=recent_content or [],
                captions=[],
                hashtags=[]
            )
        
        # Otherwise, infer from username (fallback)
        # This creates a rough embedding based on username keywords
        inferred_content = self._infer_content_from_username(username)
        
        return embedding_service.encode_text(inferred_content)
    
    def _infer_content_from_username(self, username: str) -> str:
        """
        Infer content type from username.
        This is a fallback when no profile data is available.
        """
        u_lower = username.lower()
        
        # Build a description based on username keywords
        keywords = []
        
        # Tech/Coding keywords (expanded)
        tech_keywords = ["code", "dev", "program", "tech", "js", "python", "react", 
                        "engineer", "software", "web", "app", "coding", "developer",
                        "frontend", "backend", "fullstack", "data", "ml", "ai"]
        if any(w in u_lower for w in tech_keywords):
            keywords.append("coding tutorials programming software development engineering technology")
        
        # Fitness keywords
        if any(w in u_lower for w in ["fit", "gym", "muscle", "workout", "health", "gains", "body", "training"]):
            keywords.append("fitness training bodybuilding workout exercise health")
        
        # Finance keywords
        if any(w in u_lower for w in ["money", "finance", "invest", "stock", "crypto", "wealth", "trading", "business"]):
            keywords.append("finance investing money stocks wealth building business")
        
        # Gaming keywords
        if any(w in u_lower for w in ["game", "gaming", "play", "stream", "fps", "rpg", "gamer"]):
            keywords.append("gaming gameplay streaming video games")
        
        # Lifestyle keywords
        if any(w in u_lower for w in ["vlog", "life", "travel", "minimal", "aesthetic", "lifestyle"]):
            keywords.append("lifestyle vlogging daily life content")
        
        if not keywords:
            # Default to general content
            keywords.append("content creator social media")
        
        return " ".join(keywords)
    
    def _find_similar_creators(
        self, 
        user_embedding: np.ndarray, 
        user_id: Optional[str] = None,
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Find K most similar creators using FAISS.
        
        Args:
            user_embedding: User's content vector
            user_id: Optional user ID for filtering
            k: Number of results
            
        Returns:
            List of creator suggestions with similarity scores
        """
        # Search FAISS index
        matches = vector_store.search_similar(
            user_embedding,
            k=k * 2,  # Get more for filtering
            min_similarity=0.3
        )
        
        # Filter out already selected/rejected if user_id provided
        if user_id:
            matches = [
                m for m in matches
                if not user_preferences_service.is_creator_selected(user_id, m.creator_id)
                and not user_preferences_service.is_creator_rejected(user_id, m.creator_id)
            ]
        
        # Take top K
        matches = matches[:k]
        
        # Convert to response format
        suggestions = []
        for match in matches:
            creator = creator_database.get_creator_by_id(match.creator_id)
            if creator:
                suggestions.append({
                    'id': creator['id'],
                    'name': creator['name'],
                    'handle': str(creator.get('handle') or f"@{creator['name'].lower().replace(' ', '')}"),
                    'avatar': self._get_avatar_url(creator['name']),
                    'subs': self._format_follower_count(creator['follower_count']),
                    'tags': creator['tags'],
                    'content_style': creator.get('content_style', ''),
                    'avg_views': creator.get('avg_views', 'N/A'),
                    'confidence_score': round(match.similarity_score * 100, 1),
                    'match_reason': self._generate_match_reason(creator, match.similarity_score),
                    'platform': creator['platform']
                })
        
        return suggestions
    
    def _generate_match_reason(self, creator: Dict[str, Any], similarity: float) -> str:
        """
        Generate explainable match reason.
        """
        tags = creator.get('tags', [])
        
        if similarity > 0.8:
            return f"Very similar content: {', '.join(tags[:3])}"
        elif similarity > 0.6:
            return f"Matches your interest in {', '.join(tags[:2])}"
        else:
            return f"Related to {tags[0] if tags else 'your niche'}"
    
    def _infer_niche_from_suggestions(self, suggestions: List[Dict[str, Any]]) -> str:
        """
        Infer niche from top suggestions' tags.
        """
        if not suggestions:
            return "general"
        
        # Count tag frequencies
        tag_counts = {}
        for suggestion in suggestions[:3]:  # Use top 3
            for tag in suggestion.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get most common tag
        if tag_counts:
            most_common = max(tag_counts, key=tag_counts.get)
            return most_common
        
        return "general"
    
    def get_similar_creators(
        self, 
        selected_ids: List[str], 
        user_id: Optional[str] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get "More Like This" suggestions using selected cluster centroid.
        
        Args:
            selected_ids: IDs of selected creators
            user_id: User ID for personalization
            limit: Number of suggestions
            
        Returns:
            Similar creators near selected cluster, far from rejected
        """
        if not selected_ids:
            return []
        
        # Get embeddings of selected creators
        selected_embeddings = []
        for creator_id in selected_ids:
            embedding = vector_store.get_creator_embedding(creator_id)
            if embedding is not None:
                selected_embeddings.append(embedding)
        
        if not selected_embeddings:
            return []
        
        # Calculate centroid of selected creators
        selected_centroid = np.mean(selected_embeddings, axis=0)
        
        # Search near this centroid
        matches = vector_store.search_similar(
            selected_centroid,
            k=limit * 2,
            min_similarity=0.4
        )
        
        # Filter out already selected/rejected
        if user_id:
            matches = [
                m for m in matches
                if m.creator_id not in selected_ids
                and not user_preferences_service.is_creator_rejected(user_id, m.creator_id)
            ]
        else:
            matches = [m for m in matches if m.creator_id not in selected_ids]
        
        # Convert to response format
        suggestions = []
        for match in matches[:limit]:
            creator = creator_database.get_creator_by_id(match.creator_id)
            if creator:
                handle_val = str(creator.get('handle') or f"@{creator['name'].lower().replace(' ', '')}")
                
                suggestions.append({
                    'id': creator['id'],
                    'name': creator['name'],
                    'handle': handle_val,
                    'avatar': self._get_avatar_url(creator['name']),
                    'subs': self._format_follower_count(creator['follower_count']),
                    'tags': creator['tags'],
                    'content_style': creator.get('content_style', ''),
                    'avg_views': creator.get('avg_views', 'N/A'),
                    'confidence_score': round(match.similarity_score * 100, 1),
                    'match_reason': f"Similar to your selected creators",
                    'platform': creator['platform']
                })
        
        return suggestions
    
    def _get_avatar_url(self, name: str, size: int = 200) -> str:
        """Generate avatar URL using UI Avatars API"""
        import hashlib
        name_hash = int(hashlib.md5(name.encode()).hexdigest(), 16)
        colors = [
            "FF6B6B", "4ECDC4", "45B7D1", "FFA07A", "98D8C8",
            "F7DC6F", "BB8FCE", "85C1E2", "F8B739", "52B788"
        ]
        bg_color = colors[name_hash % len(colors)]
        return f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size={size}&background={bg_color}&color=fff&bold=true&format=png"
    
    def _format_follower_count(self, count: int) -> str:
        """Format follower count (e.g., 1500000 -> 1.5M)"""
        if count >= 1000000:
            return f"{count / 1000000:.1f}M"
        elif count >= 1000:
            return f"{count / 1000:.0f}K"
        return str(count)


profile_analyzer = ProfileAnalyzer()
