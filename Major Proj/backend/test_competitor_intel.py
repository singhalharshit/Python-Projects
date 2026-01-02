"""
Test Competitor Intelligence - "Gap Analysis"
Verifies that the system can track competitors and adjust advice
"""
import sys
from pathlib import Path
import logging

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.recommendation_engine import RecommendationEngine

def test_competitor_intelligence():
    print("\n" + "🕵️ " + "="*76 + " 🕵️")
    print("   TEST: Competitor 'Gap Analysis'")
    print("🕵️ " + "="*76 + " 🕵️")
    
    engine = RecommendationEngine()
    
    # 1. Simulate User "Love Babbar" (Tech Educator)
    niche = "tech_creators"
    keywords = ["software engineering", "coding interview", "system design"]
    
    # 2. Add Competitors (Real Channel IDs)
    # Using real IDs for testing RSS fetch (these are examples, might need valid ones)
    # Fraz: UC... (Replacing with a known tech channel ID for test)
    # Let's use 'Google Developers' and 'Fireship' IDs for reliable testing
    competitors = [
        "UC_x5XG1OV2P6uZZ5FSM9Ttw", # Google Developers
        "UCsBjURrPoezykLs9EqgamOA", # Fireship
    ]
    
    user_preferences = {
        "competitors": competitors,
        "brand_voice": "deep_dive"
    }
    
    print(f"\n👤 User Context:")
    print(f"   Role: Tech Educator")
    print(f"   Tracking Competitors: {len(competitors)} channels")
    print(f"   Brand Voice: Deep Dive")
    
    print("\n⏳ Generating recommendation with Competitor Analysis...")
    print("   (This checks recent competitor videos via RSS)")
    
    recommendation = engine.generate_recommendation(
        niche, 
        keywords,
        user_preferences=user_preferences
    )
    
    print("\n" + "="*80)
    print("📊 RESULT")
    print("="*80)
    
    if recommendation['status'] == 'success':
        topic = recommendation['topic']
        print(f"\n🎯 Recommended Topic: {topic.upper()}")
        
        # Check for competitor advice
        explanation = recommendation['explanation']
        
        print(f"\n💡 Start of Explanation:")
        print(f"   {explanation.splitlines()[0]}")
        
        if "Differentiation Needed" in explanation or "Green Light" in explanation:
            print(f"\n✅ COMPETITOR INTELLIGENCE ACTIVE!")
            print("-" * 40)
            # Print last part of explanation which contains the advice
            print(f"   {explanation.splitlines()[-1]}")
            print("-" * 40)
        else:
            print("\n⚠️  No competitor advice found (maybe no overlap or error?)")
            
        # Show metadata
        meta = recommendation.get('metadata', {}).get('competitor_analysis', {})
        if meta:
            print(f"\n📈 Check Details:")
            print(f"   Status: {meta.get('status')}")
            print(f"   Is Saturated: {meta.get('is_saturated')}")
            if meta.get('videos'):
                print(f"   Found {len(meta['videos'])} overlapping videos")
    else:
        print(f"❌ Failed to generate recommendation: {recommendation['status']}")

if __name__ == "__main__":
    test_competitor_intelligence()
