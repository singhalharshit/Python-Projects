"""
Embedding Service
Core ML service for generating semantic embeddings using sentence-transformers
"""
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generates semantic embeddings for text using sentence-transformers.
    Uses all-MiniLM-L6-v2 model (384 dimensions, fast, good quality).
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """
        Initialize the embedding model.
        Model is loaded once and cached for performance.
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to encode
            
        Returns:
            numpy array of shape (384,)
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim)
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (more efficient).
        
        Args:
            texts: List of texts to encode
            
        Returns:
            numpy array of shape (n, 384)
        """
        if not texts:
            return np.zeros((0, self.embedding_dim))
        
        # Filter out empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    
    def generate_user_vector(
        self, 
        bio: str = "", 
        titles: List[str] = None, 
        captions: List[str] = None,
        hashtags: List[str] = None
    ) -> np.ndarray:
        """
        Generate user content vector from their profile data.
        
        This is the "taste vector" - represents the user's content style.
        
        Args:
            bio: User's bio/description
            titles: List of video/post titles
            captions: List of post captions
            hashtags: List of hashtags used
            
        Returns:
            Mean embedding vector (384,)
        """
        corpus = []
        
        # Add bio (weighted more heavily)
        if bio and bio.strip():
            corpus.extend([bio] * 2)  # Add twice for more weight
        
        # Add titles
        if titles:
            corpus.extend([t for t in titles if t and t.strip()])
        
        # Add captions
        if captions:
            corpus.extend([c for c in captions if c and c.strip()])
        
        # Add hashtags (join into phrases)
        if hashtags:
            hashtag_text = " ".join([h for h in hashtags if h and h.strip()])
            if hashtag_text:
                corpus.append(hashtag_text)
        
        if not corpus:
            logger.warning("Empty corpus for user vector generation")
            return np.zeros(self.embedding_dim)
        
        # Generate embeddings for all content
        embeddings = self.encode_batch(corpus)
        
        # Return mean vector (this is the user's "location" in content space)
        user_vector = np.mean(embeddings, axis=0)
        
        logger.info(f"Generated user vector from {len(corpus)} content pieces")
        return user_vector
    
    def generate_creator_vector(
        self,
        bio: str = "",
        content_samples: List[str] = None,
        tags: List[str] = None
    ) -> np.ndarray:
        """
        Generate creator content vector from their content.
        
        Args:
            bio: Creator's bio
            content_samples: Sample titles/descriptions
            tags: Content tags/categories
            
        Returns:
            Mean embedding vector (384,)
        """
        corpus = []
        
        if bio and bio.strip():
            corpus.append(bio)
        
        if content_samples:
            corpus.extend([c for c in content_samples if c and c.strip()])
        
        if tags:
            tag_text = " ".join([t for t in tags if t and t.strip()])
            if tag_text:
                corpus.append(tag_text)
        
        if not corpus:
            return np.zeros(self.embedding_dim)
        
        embeddings = self.encode_batch(corpus)
        return np.mean(embeddings, axis=0)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Returns:
            Similarity score between 0 and 1 (1 = identical)
        """
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)
        
        # Cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        
        # Clamp to [0, 1] range
        return float(max(0.0, min(1.0, similarity)))


# Global singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    Model is loaded once and reused for all requests.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


# Convenience alias
embedding_service = get_embedding_service()
