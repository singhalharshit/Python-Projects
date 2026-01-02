"""
Vector Store
FAISS-based vector similarity search for creator recommendations
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import faiss
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CreatorMatch:
    """Represents a creator match from similarity search"""
    creator_id: str
    similarity_score: float
    metadata: Dict[str, Any]


class VectorStore:
    """
    FAISS-based vector store for fast similarity search.
    Stores creator embeddings and finds nearest neighbors.
    """
    
    def __init__(self, embedding_dim: int = 384):
        """
        Initialize FAISS index.
        
        Args:
            embedding_dim: Dimension of embeddings (384 for all-MiniLM-L6-v2)
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.creator_ids = []
        self.metadata_store = {}
        
        logger.info(f"Initialized VectorStore with dimension {embedding_dim}")
    
    def build_index(self, creator_embeddings: np.ndarray, creator_ids: List[str], metadata: List[Dict[str, Any]]):
        """
        Build FAISS index from creator embeddings.
        
        Args:
            creator_embeddings: numpy array of shape (n_creators, 384)
            creator_ids: List of creator IDs
            metadata: List of metadata dicts for each creator
        """
        n_creators = len(creator_ids)
        
        if creator_embeddings.shape[0] != n_creators:
            raise ValueError(f"Mismatch: {creator_embeddings.shape[0]} embeddings but {n_creators} IDs")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(creator_embeddings)
        
        # Create FAISS index (Inner Product = cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(creator_embeddings.astype('float32'))
        
        # Store metadata
        self.creator_ids = creator_ids
        self.metadata_store = {cid: meta for cid, meta in zip(creator_ids, metadata)}
        
        logger.info(f"Built FAISS index with {n_creators} creators")
    
    def search_similar(
        self, 
        user_vector: np.ndarray, 
        k: int = 10,
        min_similarity: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CreatorMatch]:
        """
        Find K most similar creators to user vector.
        
        Args:
            user_vector: User embedding (384,)
            k: Number of results to return
            min_similarity: Minimum similarity threshold
            filters: Optional metadata filters (e.g., {'platform': 'youtube'})
            
        Returns:
            List of CreatorMatch objects sorted by similarity
        """
        if self.index is None:
            logger.error("Index not built yet!")
            return []
        
        # Normalize user vector
        user_vector_norm = user_vector.copy().reshape(1, -1).astype('float32')
        faiss.normalize_L2(user_vector_norm)
        
        # Search for more candidates than needed (for filtering)
        search_k = min(k * 3, self.index.ntotal)
        distances, indices = self.index.search(user_vector_norm, search_k)
        
        # Convert to CreatorMatch objects
        matches = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.creator_ids):
                continue
            
            creator_id = self.creator_ids[idx]
            similarity = float(dist)  # Already cosine similarity due to normalization
            
            # Skip if below threshold
            if similarity < min_similarity:
                continue
            
            metadata = self.metadata_store.get(creator_id, {})
            
            # Apply filters
            if filters:
                if not self._matches_filters(metadata, filters):
                    continue
            
            matches.append(CreatorMatch(
                creator_id=creator_id,
                similarity_score=similarity,
                metadata=metadata
            ))
        
        # Sort by similarity and return top K
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:k]
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches all filters.
        
        Args:
            metadata: Creator metadata
            filters: Filter criteria
            
        Returns:
            True if all filters match
        """
        for key, value in filters.items():
            if key == 'follower_range':
                # Special handling for follower range (±50%)
                creator_followers = metadata.get('follower_count', 0)
                target_followers = value
                
                if creator_followers == 0 or target_followers == 0:
                    continue
                
                ratio = creator_followers / target_followers
                if ratio < 0.5 or ratio > 2.0:  # Outside ±50% range
                    return False
            
            elif key == 'language':
                if metadata.get('language', '').lower() != value.lower():
                    return False
            
            elif key == 'platform':
                if metadata.get('platform', '').lower() != value.lower():
                    return False
            
            else:
                # Generic equality check
                if metadata.get(key) != value:
                    return False
        
        return True
    
    def add_creator(self, creator_id: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        """
        Add a single creator to the index.
        
        Args:
            creator_id: Unique creator ID
            embedding: Creator embedding vector
            metadata: Creator metadata
        """
        if self.index is None:
            # Initialize index if not exists
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Normalize and add
        embedding_norm = embedding.copy().reshape(1, -1).astype('float32')
        faiss.normalize_L2(embedding_norm)
        self.index.add(embedding_norm)
        
        # Store metadata
        self.creator_ids.append(creator_id)
        self.metadata_store[creator_id] = metadata
        
        logger.info(f"Added creator {creator_id} to index")
    
    def get_creator_embedding(self, creator_id: str) -> Optional[np.ndarray]:
        """
        Get embedding for a specific creator.
        
        Args:
            creator_id: Creator ID
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            idx = self.creator_ids.index(creator_id)
            # Reconstruct from FAISS index
            embedding = self.index.reconstruct(idx)
            return embedding
        except (ValueError, RuntimeError):
            return None
    
    def save_index(self, filepath: str):
        """Save FAISS index to disk"""
        if self.index is not None:
            faiss.write_index(self.index, filepath)
            logger.info(f"Saved index to {filepath}")
    
    def load_index(self, filepath: str):
        """Load FAISS index from disk"""
        self.index = faiss.read_index(filepath)
        logger.info(f"Loaded index from {filepath}")
    
    def get_all_creators(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all creators with their embeddings and metadata.
        
        Args:
            limit: Optional limit on number to return
        
        Returns:
            List of creator data dicts with user_id, embedding, metadata
        """
        creators = []
        
        for i, creator_id in enumerate(self.creator_ids):
            if limit and len(creators) >= limit:
                break
            
            # Get embedding from index
            try:
                embedding_vector = self.index.reconstruct(i)
            except:
                embedding_vector = None
            
            # Create CreatorEmbedding-like structure
            from app.services.signals.abstract_signal import CreatorEmbedding
            from datetime import datetime
            
            if embedding_vector is not None:
                # Create a minimal CreatorEmbedding
                embedding = CreatorEmbedding(
                    theme=embedding_vector,
                    tone=np.zeros(5),  # Placeholder
                    format=np.zeros(4),  # Placeholder
                    trajectory=np.zeros(4),  # Placeholder
                    creator_id=creator_id,
                    platform=self.metadata_store.get(creator_id, {}).get('platform', 'unknown'),
                    analyzed_at=datetime.utcnow(),
                    post_count=0
                )
                
                creators.append({
                    'user_id': creator_id,
                    'embedding': embedding,
                    'metadata': self.metadata_store.get(creator_id, {})
                })
        
        return creators
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 50,
        return_distances: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Alias for search_similar with different return format.
        Used by competitor discovery and niche discovery.
        
        Args:
            query_vector: Query embedding vector
            k: Number of neighbors to return
            return_distances: Whether to include distances
        
        Returns:
            List of creator data dicts
        """
        matches = self.search_similar(
            user_vector=query_vector,
            k=k,
            min_similarity=0.0  # No threshold for this method
        )
        
        results = []
        for match in matches:
            # Get embedding
            try:
                idx = self.creator_ids.index(match.creator_id)
                embedding_vector = self.index.reconstruct(idx)
            except:
                continue
            
            from app.services.signals.abstract_signal import CreatorEmbedding
            from datetime import datetime
            
            embedding = CreatorEmbedding(
                theme=embedding_vector,
                tone=np.zeros(5),
                format=np.zeros(4),
                trajectory=np.zeros(4),
                creator_id=match.creator_id,
                platform=match.metadata.get('platform', 'unknown'),
                analyzed_at=datetime.utcnow(),
                post_count=0
            )
            
            result = {
                'user_id': match.creator_id,
                'embedding': embedding,
                'metadata': match.metadata
            }
            
            if return_distances:
                result['distance'] = 1 - match.similarity_score  # Convert similarity to distance
            
            results.append(result)
        
        return results


# Global singleton
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


vector_store = get_vector_store()
