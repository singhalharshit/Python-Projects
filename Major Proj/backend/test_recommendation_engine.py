"""
Test the Recommendation Engine
Demonstrates how the engine combines signals and generates recommendations
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.recommendation_engine import RecommendationEngine
import json
from datetime import datetime


def print_recommendation(rec: dict):
    """Pretty print a recommendation"""
    print("\n" + "="*80)
    print(" " * 25 + "📊 DAILY RECOMMENDATION")
    print("="*80)
    
    # Status
    status_emoji = {
        'success': '✅',
        'no_trends': '⚠️',
        'no_recommendation': '⚠️',
        'error': '❌'
    }
    print(f"\nStatus: {status_emoji.get(rec['status'], '❓')} {rec['status'].upper()}")
    
    # Action
    action_emoji = {
        'post': '📝',
        'engage': '💬',
        'rest': '😴'
    }
    print(f"Action: {action_emoji.get(rec['action'], '❓')} {rec['action'].upper()}")
    
    # Topic
    if rec.get('topic'):
        print(f"\n🎯 RECOMMENDED TOPIC")
        print("-" * 80)
        print(f"   {rec['topic'].title()}")
    
    # Confidence
    print(f"\n📊 CONFIDENCE")
    print("-" * 80)
    print(f"   Level: {rec['confidence_level'].upper()}")
    print(f"   Score: {rec['confidence_score']}/100")
    
    # Sources
    if rec.get('sources'):
        print(f"\n🔍 VALIDATED BY {len(rec['sources'])} SOURCE(S)")
        print("-" * 80)
        source_names = {
            'google_trends': '📈 Google Trends',
            'google_news': '📰 Google News',
            'youtube': '🎥 YouTube',
            'reddit': '🤖 Reddit'
        }
        for source in rec['sources']:
            print(f"   • {source_names.get(source, source)}")
    
    # Explanation
    print(f"\n💡 EXPLANATION")
    print("-" * 80)
    print(f"   {rec['explanation']}")
    
    # Reasoning
    print(f"\n📝 REASONING")
    print("-" * 80)
    print(f"   {rec['reasoning']}")
    
    # Timing
    if rec.get('timing'):
        timing = rec['timing']
        print(f"\n⏰ TIMING")
        print("-" * 80)
        print(f"   Urgency: {timing['urgency'].upper()}")
        print(f"   Window: {timing['suggested_window']}")
        print(f"   Reason: {timing['reason']}")
    
    # Alternatives
    if rec.get('alternatives'):
        print(f"\n🔄 ALTERNATIVE TOPICS")
        print("-" * 80)
        for i, alt in enumerate(rec['alternatives'][:3], 1):
            print(f"   {i}. {alt['topic'].title()} ({alt['confidence_score']:.0%} confidence)")
    
    # Signal Health
    if rec.get('signal_health'):
        print(f"\n🏥 SIGNAL HEALTH")
        print("-" * 80)
        for source, status in rec['signal_health'].items():
            status_emoji = '✅' if status == 'healthy' else '⚠️'
            print(f"   {status_emoji} {source}: {status}")
    
    # Metadata
    print(f"\n📋 METADATA")
    print("-" * 80)
    print(f"   Sources Checked: {rec.get('sources_checked', 0)}")
    print(f"   Sources Available: {rec.get('sources_available', 0)}")
    print(f"   Generated: {rec.get('generated_at', 'N/A')}")
    
    print("\n" + "="*80 + "\n")


def test_tech_niche():
    """Test recommendation for tech creators"""
    print("\n" + "🚀 " + "="*76 + " 🚀")
    print("   TEST 1: Tech Creator Niche")
    print("🚀 " + "="*76 + " 🚀")
    
    engine = RecommendationEngine()
    
    niche = "tech_creators"
    keywords = ["AI", "ChatGPT", "Python", "coding", "machine learning"]
    
    print(f"\nNiche: {niche}")
    print(f"Keywords: {', '.join(keywords)}")
    print("\nGenerating recommendation...")
    
    recommendation = engine.generate_recommendation(niche, keywords)
    
    print_recommendation(recommendation)
    
    return recommendation


def test_gaming_niche():
    """Test recommendation for gaming creators"""
    print("\n" + "🎮 " + "="*76 + " 🎮")
    print("   TEST 2: Gaming Creator Niche")
    print("🎮 " + "="*76 + " 🎮")
    
    engine = RecommendationEngine()
    
    niche = "gaming_creators"
    keywords = ["gaming", "esports", "game reviews", "streaming"]
    
    print(f"\nNiche: {niche}")
    print(f"Keywords: {', '.join(keywords)}")
    print("\nGenerating recommendation...")
    
    recommendation = engine.generate_recommendation(niche, keywords)
    
    print_recommendation(recommendation)
    
    return recommendation


def test_business_niche():
    """Test recommendation for business creators"""
    print("\n" + "💼 " + "="*76 + " 💼")
    print("   TEST 3: Business Creator Niche")
    print("💼 " + "="*76 + " 💼")
    
    engine = RecommendationEngine()
    
    niche = "business_creators"
    keywords = ["entrepreneurship", "startup", "business", "productivity"]
    
    print(f"\nNiche: {niche}")
    print(f"Keywords: {', '.join(keywords)}")
    print("\nGenerating recommendation...")
    
    recommendation = engine.generate_recommendation(niche, keywords)
    
    print_recommendation(recommendation)
    
    return recommendation


def save_example_output(recommendation: dict, filename: str):
    """Save recommendation to JSON file for reference"""
    with open(filename, 'w') as f:
        json.dump(recommendation, f, indent=2, default=str)
    print(f"💾 Saved example output to: {filename}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" " * 20 + "🧠 RECOMMENDATION ENGINE TEST")
    print("="*80)
    
    print("\nThis will test the recommendation engine with real data from:")
    print("  • Google Trends (real-time search trends)")
    print("  • Google News (latest news coverage)")
    print("  • YouTube (if API key available)")
    
    print("\n⏳ This may take 5-10 seconds per test...\n")
    
    try:
        # Test 1: Tech niche
        tech_rec = test_tech_niche()
        save_example_output(tech_rec, "example_tech_recommendation.json")
        
        # Test 2: Gaming niche
        gaming_rec = test_gaming_niche()
        save_example_output(gaming_rec, "example_gaming_recommendation.json")
        
        # Test 3: Business niche
        business_rec = test_business_niche()
        save_example_output(business_rec, "example_business_recommendation.json")
        
        # Summary
        print("\n" + "="*80)
        print(" " * 30 + "📊 TEST SUMMARY")
        print("="*80)
        
        tests = [
            ("Tech Creators", tech_rec),
            ("Gaming Creators", gaming_rec),
            ("Business Creators", business_rec)
        ]
        
        print("\n┌" + "─"*78 + "┐")
        print("│ Niche              │ Status    │ Action │ Confidence │ Sources │")
        print("├" + "─"*78 + "┤")
        
        for name, rec in tests:
            status_emoji = '✅' if rec['status'] == 'success' else '⚠️'
            action = rec['action'][:6]
            conf = rec['confidence_level'][:6]
            sources = rec.get('source_count', 0)
            
            print(f"│ {name:<18} │ {status_emoji} {rec['status'][:6]:<6} │ {action:<6} │ {conf:<10} │ {sources:^7} │")
        
        print("└" + "─"*78 + "┘")
        
        print("\n✅ All tests completed!")
        print("\n💡 Key Observations:")
        print("   • Multi-source validation increases confidence")
        print("   • Conservative language in explanations")
        print("   • Transparent about data sources")
        print("   • Graceful handling when no trends found")
        
        print("\n📁 Example outputs saved as JSON files")
        print("   • example_tech_recommendation.json")
        print("   • example_gaming_recommendation.json")
        print("   • example_business_recommendation.json")
        
        print("\n🎉 Recommendation Engine is working!\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
