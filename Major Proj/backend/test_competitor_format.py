"""
Test Competitor Data Format
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from app.services.intelligence.competitor_discovery import CompetitorProfile
    from app.services.signals.abstract_signal import CreatorEmbedding
    import numpy as np
    from datetime import datetime
    
    # Create a mock competitor
    mock_embedding = CreatorEmbedding(
        theme=np.random.rand(384),
        tone=np.random.rand(5),
        format=np.random.rand(4),
        trajectory=np.random.rand(4),
        creator_id="test_creator_123",
        platform="instagram",
        analyzed_at=datetime.utcnow(),
        post_count=50
    )
    
    competitor = CompetitorProfile(
        creator_id="competitor_456",
        embedding=mock_embedding,
        relevance=0.85,
        differentiation=0.65,
        aspirational_distance=0.75,
        total_score=0.78,
        platform="instagram",
        follower_count=10000,
        engagement_rate=0.045
    )
    
    # Convert to dict
    comp_dict = competitor.to_dict()
    
    print("Competitor data structure:")
    print("="*60)
    import json
    print(json.dumps(comp_dict, indent=2))
    print("="*60)
    
    # Check for required fields
    required = ['creator_id', 'platform', 'scores']
    print("\nRequired fields check:")
    for field in required:
        present = field in comp_dict
        print(f"  {field}: {'✅' if present else '❌'}")
    
    # Check what frontend expects
    print("\nFrontend expects:")
    print("  - name (creator name)")
    print("  - subs (subscriber count)")
    print("  - avatar (profile picture)")
    print("  - tags (content tags)")
    print("  - confidence_score")
    print("  - match_reason")
    
    print("\n⚠️  ISSUE: Backend returns 'creator_id' but frontend expects 'name', 'subs', etc.")
