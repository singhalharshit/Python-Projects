"""
Dynamic Niche Discovery System

NO HARDCODED CATEGORIES.
Discovers niches organically from creator content embeddings.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from collections import Counter
import hashlib

from app.services.intelligence.embedding_service import EmbeddingService
from app.models.creator import CreatorProfile

logger = logging.getLogger(__name__)


@dataclass
class DynamicNiche:
    """
    A dynamically discovered niche cluster.
    
    NOT a predefined category.
    Emerges from actual creator content patterns.
    """
    id: str
    name: str  # Generated from semantic descriptors
    embedding_centroid: np.ndarray
    member_count: int
    is_micro: bool  # True if < 5 members (unique/rare niche)
    descriptors: List[str]  # Top semantic descriptors
    created_at: str
    last_updated: str


class DynamicNicheDiscovery:
    """
    Discovers niches from creator embeddings using unsupervised clustering.
    
    Philosophy:
    - NO predefined categories
    - Structure emerges from data
    - Micro-niches are valid (allows uniqueness)
    - Niches can overlap (creators can belong to multiple)
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.niche_cache: Dict[str, DynamicNiche] = {}
        
    def discover_user_niche(
        self,
        user_profile: CreatorProfile,
        context_creators: List[CreatorProfile],
        min_cluster_size: int = 3
    ) -> DynamicNiche:
        """
        Discover which niche cluster this user belongs to.
        
        Process:
        1. Embed user and context creators
        2. Find natural clusters using DBSCAN (allows outliers)
        3. Assign user to cluster or create micro-niche
        
        Args:
            user_profile: The creator we're analyzing
            context_creators: Similar creators for context (50-200 recommended)
            min_cluster_size: Minimum members for a standard niche
            
        Returns:
            DynamicNiche object (either existing cluster or new micro-niche)
        """
        logger.info(f"Discovering niche for user with {len(context_creators)} context creators")
        
        # Get embeddings
        user_embedding = self.embedding_service.embed_creator_profile(user_profile)
        context_embeddings = [
            self.embedding_service.embed_creator_profile(creator)
            for creator in context_creators
        ]
        
        # Stack all embeddings (user first)
        all_embeddings = np.vstack([user_embedding] + context_embeddings)
        
        # Perform density-based clustering
        clustering = DBSCAN(
            eps=0.3,  # Similarity threshold
            min_samples=min_cluster_size,
            metric='cosine'
        ).fit(all_embeddings)
        
        user_cluster_label = clustering.labels_[0]
        
        if user_cluster_label == -1:
            # User is an outlier - this is a MICRO-NICHE (unique creator)
            logger.info("User is outlier - creating micro-niche")
            return self._create_micro_niche(user_profile, user_embedding)
        else:
            # User fits into existing cluster
            cluster_members = [
                (context_creators[i-1], context_embeddings[i-1])  # -1 because user is first
                for i, label in enumerate(clustering.labels_)
                if label == user_cluster_label and i > 0
            ]
            cluster_members.append((user_profile, user_embedding))
            
            logger.info(f"User fits cluster {user_cluster_label} with {len(cluster_members)} members")
            return self._get_or_create_niche_cluster(
                cluster_label=user_cluster_label,
                members=cluster_members
            )
    
    def _create_micro_niche(
        self,
        creator: CreatorProfile,
        embedding: np.ndarray
    ) -> DynamicNiche:
        """
        Create a micro-niche for unique creators.
        
        This is NOT a failure - micro-niches are valid.
        They represent unique positioning.
        """
        
        # Extract semantic descriptors from content
        descriptors = self.embedding_service.extract_semantic_keywords(
            creator.content_sample,
            top_k=3
        )
        
        # Generate unique ID from embedding
        niche_id = f"micro_{hashlib.md5(embedding.tobytes()).hexdigest()[:8]}"
        
        # Generate name from descriptors
        name = f"{descriptors[0].title()} + {descriptors[1].title()}" if len(descriptors) >= 2 else f"Unique {descriptors[0].title()}"
        
        micro_niche = DynamicNiche(
            id=niche_id,
            name=name,
            embedding_centroid=embedding,
            member_count=1,
            is_micro=True,
            descriptors=descriptors,
            created_at=str(np.datetime64('now')),
            last_updated=str(np.datetime64('now'))
        )
        
        logger.info(f"Created micro-niche: {name}")
        return micro_niche
    
    def _get_or_create_niche_cluster(
        self,
        cluster_label: int,
        members: List[Tuple[CreatorProfile, np.ndarray]]
    ) -> DynamicNiche:
        """
        Get existing niche or create new one from cluster.
        """
        
        # Calculate cluster centroid
        embeddings = np.array([emb for _, emb in members])
        centroid = np.mean(embeddings, axis=0)
        
        # Generate unique ID from centroid
        niche_id = f"cluster_{hashlib.md5(centroid.tobytes()).hexdigest()[:8]}"
        
        # Check cache
        if niche_id in self.niche_cache:
            cached_niche = self.niche_cache[niche_id]
            cached_niche.member_count = len(members)
            cached_niche.last_updated = str(np.datetime64('now'))
            return cached_niche
        
        # Create new niche
        # Extract common themes from all members
        all_content = " ".join([creator.content_sample for creator, _ in members])
        descriptors = self.embedding_service.extract_semantic_keywords(
            all_content,
            top_k=5
        )
        
        # Generate name from top descriptors
        name = f"{descriptors[0].title()} & {descriptors[1].title()} Creators"
        
        new_niche = DynamicNiche(
            id=niche_id,
            name=name,
            embedding_centroid=centroid,
            member_count=len(members),
            is_micro=False,
            descriptors=descriptors,
            created_at=str(np.datetime64('now')),
            last_updated=str(np.datetime64('now'))
        )
        
        # Cache it
        self.niche_cache[niche_id] = new_niche
        
        logger.info(f"Created niche cluster: {name} with {len(members)} members")
        return new_niche
    
    def discover_global_niches(
        self,
        all_creators: List[CreatorProfile],
        n_clusters: Optional[int] = None
    ) -> List[DynamicNiche]:
        """
        Discover global niche landscape from large creator dataset.
        
        Use this for:
        - Analyzing the entire creator ecosystem
        - Finding blue ocean opportunities
        - Understanding niche saturation
        
        Args:
            all_creators: Large dataset of creators (1000+)
            n_clusters: Number of clusters (auto-detected if None)
            
        Returns:
            List of discovered niches
        """
        logger.info(f"Discovering global niches from {len(all_creators)} creators")
        
        # Get all embeddings
        embeddings = np.array([
            self.embedding_service.embed_creator_profile(creator)
            for creator in all_creators
        ])
        
        # Auto-detect optimal number of clusters if not provided
        if n_clusters is None:
            n_clusters = self._estimate_optimal_clusters(embeddings)
            logger.info(f"Auto-detected optimal clusters: {n_clusters}")
        
        # Perform K-Means clustering
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        ).fit(embeddings)
        
        # Create niche for each cluster
        niches = []
        for cluster_id in range(n_clusters):
            cluster_mask = kmeans.labels_ == cluster_id
            cluster_creators = [
                creator for i, creator in enumerate(all_creators)
                if cluster_mask[i]
            ]
            cluster_embeddings = embeddings[cluster_mask]
            
            if len(cluster_creators) == 0:
                continue
            
            # Create niche from cluster
            centroid = kmeans.cluster_centers_[cluster_id]
            
            # Extract themes
            all_content = " ".join([c.content_sample for c in cluster_creators[:50]])  # Sample for performance
            descriptors = self.embedding_service.extract_semantic_keywords(
                all_content,
                top_k=5
            )
            
            niche_id = f"global_{hashlib.md5(centroid.tobytes()).hexdigest()[:8]}"
            name = f"{descriptors[0].title()} & {descriptors[1].title()}"
            
            niche = DynamicNiche(
                id=niche_id,
                name=name,
                embedding_centroid=centroid,
                member_count=len(cluster_creators),
                is_micro=len(cluster_creators) < 10,
                descriptors=descriptors,
                created_at=str(np.datetime64('now')),
                last_updated=str(np.datetime64('now'))
            )
            
            niches.append(niche)
        
        logger.info(f"Discovered {len(niches)} global niches")
        return niches
    
    def _estimate_optimal_clusters(
        self,
        embeddings: np.ndarray,
        min_clusters: int = 5,
        max_clusters: int = 20
    ) -> int:
        """
        Estimate optimal number of clusters using silhouette score.
        """
        best_score = -1
        best_n = min_clusters
        
        for n in range(min_clusters, min(max_clusters, len(embeddings) // 10)):
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=3).fit(embeddings)
            score = silhouette_score(embeddings, kmeans.labels_, sample_size=min(1000, len(embeddings)))
            
            if score > best_score:
                best_score = score
                best_n = n
        
        return best_n
    
    def calculate_niche_saturation(
        self,
        niche: DynamicNiche,
        recent_content_volume: int,
        time_window_days: int = 7
    ) -> float:
        """
        Calculate how saturated this niche is.
        
        Returns:
            Saturation score 0.0-1.0
            - 0.0-0.3: Blue ocean (low saturation)
            - 0.3-0.7: Moderate competition
            - 0.7-1.0: Red ocean (highly saturated)
        """
        
        # Base saturation from member count
        # More members = more competition
        member_saturation = min(niche.member_count / 1000, 1.0)
        
        # Content velocity saturation
        # High recent posting = saturated
        content_velocity = recent_content_volume / (time_window_days * niche.member_count)
        velocity_saturation = min(content_velocity / 5.0, 1.0)  # 5 posts/day/member = saturated
        
        # Combined saturation
        saturation = (member_saturation * 0.4) + (velocity_saturation * 0.6)
        
        return saturation
