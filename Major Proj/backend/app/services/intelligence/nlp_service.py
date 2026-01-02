"""
NLP Service - The AI Brain
Uses Sentence Transformers for semantic analysis and clustering
"""
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

class NLPService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPService, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """Lazy load the model to save startup time"""
        if self._model is None:
            logger.info("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
            try:
                # Small, fast model perfect for topic similarity
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ AI Model Loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load AI model: {e}")
                self._model = None

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts (0.0 to 1.0).
        Example: "Python" vs "Coding with snake" -> High Score
        """
        self.initialize()
        if not self._model:
            return 0.0

        try:
            embeddings = self._model.encode([text1, text2], convert_to_tensor=True)
            score = util.cos_sim(embeddings[0], embeddings[1])
            return float(score.item())
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0

    def batch_similarity(self, source_text: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """Compare one text against a list of candidates efficiently"""
        self.initialize()
        if not self._model or not candidates:
            return []

        try:
            # Encode all at once
            source_emb = self._model.encode(source_text, convert_to_tensor=True)
            candidate_embs = self._model.encode(candidates, convert_to_tensor=True)
            
            scores = util.cos_sim(source_emb, candidate_embs)[0]
            
            results = []
            for idx, score in enumerate(scores):
                results.append((candidates[idx], float(score)))
                
            # Sort by highest similarity
            results.sort(key=lambda x: x[1], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Batch similarity failed: {e}")
            return []

    def cluster_topics(self, topics: List[str], num_clusters: int = 5) -> Dict[int, List[str]]:
        """
        Group similar topics together using K-Means clustering.
        Great for finding "Meta-Trends" in noisy data.
        """
        self.initialize()
        if not self._model or len(topics) < num_clusters:
            return {0: topics}

        try:
            logger.info(f"Clustering {len(topics)} topics into {num_clusters} groups...")
            embeddings = self._model.encode(topics)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            
            clusters = {}
            for idx, label in enumerate(kmeans.labels_):
                label = int(label)
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(topics[idx])
                
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {0: topics}

# Global instance
nlp_service = NLPService()
