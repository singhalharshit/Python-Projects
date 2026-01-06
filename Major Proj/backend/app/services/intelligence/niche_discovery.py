"""
Dynamic Niche Discovery Engine
Discovers niches from creator content through clustering - no hardcoding
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import uuid

from app.models.dynamic_niche import DynamicNiche
from app.services.intelligence.embedding_service import EmbeddingService
from app.services.signals.abstract_signal import CreatorEmbedding

logger = logging.getLogger(__name__)


class NicheDiscoveryEngine:
    """
    Discovers content niches dynamically through clustering.
    
    Philosophy:
    - NO hardcoded categories
    - Niches emerge from creator data
    - Semantic clustering, not keyword matching
    - Niches evolve over time
    
    Process:
    1. Collect all creator embeddings
    2. Cluster in semantic space (K-Means)
    3. Generate human-readable labels (TF-IDF)
    4. Track niche evolution
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.min_creators_per_niche = 5  # Minimum cluster size
    
    def discover_niches(
        self,
        creator_embeddings: List[CreatorEmbedding],
        n_clusters: Optional[int] = None,
        method: str = 'kmeans'
    ) -> List[DynamicNiche]:
        """
        Discover niches from creator embeddings.
        
        Args:
            creator_embeddings: List of creator embeddings
            n_clusters: Number of clusters (auto if None)
            method: 'kmeans' or 'dbscan'
        
        Returns:
            List of discovered DynamicNiche objects
        """
        if len(creator_embeddings) < self.min_creators_per_niche:
            logger.warning(
                f"Not enough creators ({len(creator_embeddings)}) "
                f"for niche discovery. Minimum: {self.min_creators_per_niche}"
            )
            return []
        
        # Extract theme vectors
        theme_vectors = np.array([c.theme for c in creator_embeddings])
        
        # Determine optimal number of clusters if not specified
        if n_clusters is None:
            n_clusters = self._estimate_optimal_clusters(theme_vectors)
        
        logger.info(
            f"Discovering niches from {len(creator_embeddings)} creators "
            f"using {method} with {n_clusters} clusters"
        )
        
        # Cluster
        if method == 'kmeans':
            cluster_labels, centroids = self._cluster_kmeans(theme_vectors, n_clusters)
        elif method == 'dbscan':
            cluster_labels, centroids = self._cluster_dbscan(theme_vectors)
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        # Create niche objects
        niches = self._create_niches_from_clusters(
            creator_embeddings,
            cluster_labels,
            centroids
        )
        
        # Store in database
        for niche in niches:
            self._store_niche(niche)
        
        logger.info(f"Discovered {len(niches)} niches")
        
        return niches
    
    def discover_niche_for_creator(
        self,
        creator_embedding: CreatorEmbedding
    ) -> Optional[DynamicNiche]:
        """
        Find which niche a creator belongs to.
        
        Args:
            creator_embedding: Creator's embedding
        
        Returns:
            DynamicNiche (creates micro-niche if no existing niches)
        """
        # Get all existing niches
        existing_niches = self.db.query(DynamicNiche).all()
        
        # ✅ FIX: If no niches exist, create a micro-niche for this creator
        if not existing_niches:
            logger.info("No niches found. Creating micro-niche for creator.")
            return self._create_micro_niche(creator_embedding)
        
        # Find nearest niche
        best_niche = None
        best_distance = float('inf')
        
        for niche in existing_niches:
            centroid = niche.get_centroid_vector()
            if centroid is None:
                continue
            
            # Calculate cosine distance
            distance = 1 - self._cosine_similarity(
                creator_embedding.theme,
                centroid
            )
            
            if distance < best_distance:
                best_distance = distance
                best_niche = niche
        
        # Check if distance is reasonable (< 0.5)
        if best_distance > 0.5:
            logger.info(
                f"Creator {creator_embedding.creator_id} doesn't fit "
                f"existing niches (distance: {best_distance:.2f})"
            )
            return None
        
        logger.info(
            f"Creator {creator_embedding.creator_id} assigned to "
            f"niche '{best_niche.label}' (distance: {best_distance:.2f})"
        )
        
        return best_niche
    
    def _estimate_optimal_clusters(self, vectors: np.ndarray) -> int:
        """
        Estimate optimal number of clusters using elbow method.
        
        Args:
            vectors: Array of embedding vectors
        
        Returns:
            Optimal number of clusters
        """
        n_samples = len(vectors)
        
        # Rule of thumb: sqrt(n/2)
        optimal = int(np.sqrt(n_samples / 2))
        
        # Constrain between 5 and 50
        optimal = max(5, min(optimal, 50))
        
        logger.info(f"Estimated optimal clusters: {optimal} for {n_samples} samples")
        
        return optimal
    
    def _cluster_kmeans(
        self,
        vectors: np.ndarray,
        n_clusters: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Cluster using K-Means.
        
        Returns:
            (cluster_labels, centroids)
        """
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        
        cluster_labels = kmeans.fit_predict(vectors)
        centroids = kmeans.cluster_centers_
        
        return cluster_labels, centroids
    
    def _cluster_dbscan(
        self,
        vectors: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Cluster using DBSCAN (density-based).
        
        Returns:
            (cluster_labels, centroids)
        """
        dbscan = DBSCAN(
            eps=0.3,  # Maximum distance between samples
            min_samples=self.min_creators_per_niche,
            metric='cosine'
        )
        
        cluster_labels = dbscan.fit_predict(vectors)
        
        # Calculate centroids for each cluster
        unique_labels = set(cluster_labels)
        unique_labels.discard(-1)  # Remove noise label
        
        centroids = []
        for label in sorted(unique_labels):
            cluster_vectors = vectors[cluster_labels == label]
            centroid = np.mean(cluster_vectors, axis=0)
            centroids.append(centroid)
        
        centroids = np.array(centroids) if centroids else np.array([])
        
        return cluster_labels, centroids
    
    def _create_niches_from_clusters(
        self,
        creator_embeddings: List[CreatorEmbedding],
        cluster_labels: np.ndarray,
        centroids: np.ndarray
    ) -> List[DynamicNiche]:
        """
        Create DynamicNiche objects from clusters.
        """
        niches = []
        
        unique_labels = set(cluster_labels)
        unique_labels.discard(-1)  # Remove noise label
        
        for cluster_id in sorted(unique_labels):
            # Get creators in this cluster
            cluster_mask = cluster_labels == cluster_id
            cluster_creators = [
                c for i, c in enumerate(creator_embeddings)
                if cluster_mask[i]
            ]
            
            if len(cluster_creators) < self.min_creators_per_niche:
                logger.info(
                    f"Skipping cluster {cluster_id}: "
                    f"only {len(cluster_creators)} creators"
                )
                continue
            
            # Generate label and description
            label, description, keywords = self._generate_niche_label(
                cluster_creators
            )
            
            # Calculate cluster statistics
            cluster_vectors = np.array([c.theme for c in cluster_creators])
            centroid = centroids[cluster_id]
            
            # Calculate radius (average distance from centroid)
            distances = [
                1 - self._cosine_similarity(v, centroid)
                for v in cluster_vectors
            ]
            radius = float(np.mean(distances))
            
            # Calculate density (inverse of variance)
            density = float(1.0 / (np.var(distances) + 1e-6))
            
            # Create niche
            niche = DynamicNiche(
                id=str(uuid.uuid4()),
                label=label,
                description=description,
                cluster_id=int(cluster_id),
                creator_count=len(cluster_creators),
                cluster_radius=radius,
                cluster_density=density,
                keywords=keywords,
                example_creators=[c.creator_id for c in cluster_creators[:5]],
                first_discovered=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            niche.set_centroid_vector(centroid)
            
            niches.append(niche)
            
            logger.info(
                f"Created niche '{label}': "
                f"{len(cluster_creators)} creators, "
                f"radius={radius:.3f}, density={density:.3f}"
            )
        
        return niches
    
    def _generate_niche_label(
        self,
        cluster_creators: List[CreatorEmbedding]
    ) -> tuple[str, str, List[str]]:
        """
        Generate human-readable label for a niche.
        
        Uses TF-IDF to find distinctive terms.
        
        Returns:
            (label, description, keywords)
        """
        # Collect all text from creators (would need bio/content in real implementation)
        # For now, use a placeholder approach
        
        # Extract keywords using TF-IDF
        # In production, this would analyze creator bios and content
        
        # Placeholder: Generate label from cluster ID
        cluster_id = cluster_creators[0].creator_id.split('_')[0] if cluster_creators else "unknown"
        
        # In production implementation:
        # 1. Collect creator bios and recent post titles
        # 2. Apply TF-IDF to find distinctive terms
        # 3. Combine top 2-3 terms into label
        
        # For now, return placeholder
        label = f"niche_{cluster_id}_{len(cluster_creators)}"
        description = f"A content niche with {len(cluster_creators)} creators"
        keywords = ["content", "creators", "niche"]
        
        return label, description, keywords
    
    def _store_niche(self, niche: DynamicNiche):
        """Store or update niche in database"""
        
        # Check if niche with same label exists
        existing = self.db.query(DynamicNiche).filter_by(
            label=niche.label
        ).first()
        
        if existing:
            # Update existing
            existing.creator_count = niche.creator_count
            existing.cluster_radius = niche.cluster_radius
            existing.cluster_density = niche.cluster_density
            existing.keywords = niche.keywords
            existing.example_creators = niche.example_creators
            existing.last_updated = datetime.utcnow()
            existing.set_centroid_vector(niche.get_centroid_vector())
            
            logger.info(f"Updated existing niche: {niche.label}")
        else:
            # Add new
            self.db.add(niche)
            logger.info(f"Created new niche: {niche.label}")
        
        self.db.commit()
    
    def _create_micro_niche(self, creator_embedding: CreatorEmbedding) -> DynamicNiche:
        """
        Create a micro-niche for a single creator.
        
        This is used when:
        1. No existing niches found (first user)
        2. Creator doesn't fit any existing niche
        
        Args:
            creator_embedding: Creator's embedding
        
        Returns:
            New DynamicNiche (micro-niche)
        """
        # Generate a simple label from platform and ID
        platform = creator_embedding.platform or 'creator'
        niche_id = str(uuid.uuid4())[:8]
        label = f"{platform}_{niche_id}"
        
        # Convert embedding to list
        centroid_list = creator_embedding.theme.tolist()
        
        # Create micro-niche with ALL required fields
        micro_niche = DynamicNiche(
            id=niche_id,
            name=label,
            label=label,
            description=None,
            centroid_vector=centroid_list,  # ✅ REQUIRED field
            embedding_centroid=centroid_list,  # ✅ New field
            creator_count=1,
            cluster_id=None,
            cluster_radius=None,
            cluster_density=None,
            keywords=['unique', 'emerging', platform],
            descriptors=['unique', 'emerging', platform],
            is_micro=1,
            member_count=1,
            signal_count_7d=0,
            momentum=0.0
        )
        
        # Store in database
        self.db.add(micro_niche)
        self.db.commit()
        
        logger.info(f"✅ Created micro-niche '{label}' for creator {creator_embedding.creator_id}")
        
        return micro_niche
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def get_niche_by_label(self, label: str) -> Optional[DynamicNiche]:
        """Get niche by label"""
        return self.db.query(DynamicNiche).filter_by(label=label).first()
    
    def get_all_niches(self) -> List[DynamicNiche]:
        """Get all discovered niches"""
        return self.db.query(DynamicNiche).all()
    
    def update_niche_momentum(self, niche_id: str, signal_count: int):
        """Update niche momentum based on recent signals"""
        niche = self.db.query(DynamicNiche).filter_by(id=niche_id).first()
        
        if niche:
            niche.signal_count_7d = signal_count
            # Simple momentum calculation
            niche.momentum = min(signal_count / 100.0, 1.0)
            self.db.commit()


# ✅ Global getter function
def get_niche_discovery(db: Session) -> NicheDiscoveryEngine:
    """Get or create NicheDiscoveryEngine instance"""
    return NicheDiscoveryEngine(db)
