"""
Dynamic Niche Model
Represents discovered niches from clustering, not hardcoded categories
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Float, func
from app.core.database import Base
from datetime import datetime
from typing import List, Dict, Any
import numpy as np


class DynamicNiche(Base):
    """
    Dynamically discovered content niche through clustering.
    No hardcoded categories - all niches emerge from creator data.
    """
    __tablename__ = "dynamic_niches"
    
    id = Column(String, primary_key=True)
    
    # Semantic label (e.g., "ai_coding_education", "fitness_mindfulness")
    label = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)  # ✅ Alias for label
    
    # Human-readable description
    description = Column(String)
    
    # Centroid embedding vector (stored as JSON array)
    centroid_vector = Column(JSON, nullable=False)  # Keep NOT NULL for existing data
    embedding_centroid = Column(JSON, nullable=True)  # ✅ Renamed for consistency
    
    # Number of creators in this niche
    creator_count = Column(Integer, default=0)
    
    # Cluster statistics
    cluster_id = Column(Integer)  # K-Means cluster ID
    cluster_radius = Column(Float)  # Average distance from centroid
    cluster_density = Column(Float)  # How tightly clustered
    
    # Representative keywords
    keywords = Column(JSON)  # List of distinctive terms
    descriptors = Column(JSON)  # ✅ Alias for keywords
    
    # Niche characteristics
    is_micro = Column(Integer, default=0)  # ✅ Is this a micro-niche (1 creator)?
    member_count = Column(Integer, default=0)  # ✅ Alias for creator_count
    
    # Example creator IDs in this niche
    example_creators = Column(JSON)  # List of creator IDs
    
    # Niche evolution tracking
    first_discovered = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Activity metrics
    signal_count_7d = Column(Integer, default=0)  # Signals detected in last 7 days
    momentum = Column(Float, default=0.0)  # Overall niche momentum
    
    # Metadata
    metadata_json = Column("metadata", JSON)
    
    def to_dict(self) -> Dict[str, Any]:
        """✅ Convert to dictionary with all necessary fields"""
        return {
            'niche_id': self.id,  # ✅ Added for onboarding compatibility
            'id': self.id,
            'label': self.label,
            'name': self.name or self.label,  # ✅ Use name if exists, else label
            'description': self.description,
            'creator_count': self.creator_count,
            'keywords': self.keywords,
            'descriptors': self.descriptors or self.keywords,  # ✅ Use descriptors if exists
            'momentum': self.momentum,
            'is_micro': bool(self.is_micro),  # ✅ Convert to boolean for JSON
            'centroid': self.centroid_vector or self.embedding_centroid,  # ✅ Use either field
            'cluster_stats': {
                'radius': self.cluster_radius,
                'density': self.cluster_density
            },
            'discovered_at': self.first_discovered.isoformat() if self.first_discovered else None,
            'updated_at': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def get_centroid_vector(self) -> np.ndarray:
        """✅ Get centroid as numpy array (checks both fields)"""
        # Check embedding_centroid first (new field)
        if self.embedding_centroid:
            return np.array(self.embedding_centroid)
        # Fall back to centroid_vector (old field)
        if self.centroid_vector:
            return np.array(self.centroid_vector)
        return None
    
    def set_centroid_vector(self, vector: np.ndarray):
        """✅ Set centroid from numpy array (sets both fields)"""
        vector_list = vector.tolist()
        self.embedding_centroid = vector_list
        self.centroid_vector = vector_list  # Keep for compatibility
