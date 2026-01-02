"""
Competitor Intelligence Service
Analyzes competitor activity to tailor recommendations
"""
from typing import List, Dict, Any
import logging
from app.services.collectors.youtube_rss_collector import YouTubeRSSCollector

logger = logging.getLogger(__name__)

class CompetitorAnalysisService:
    def __init__(self):
        self.rss_collector = YouTubeRSSCollector()
    
    def analyze_topic(self, topic: str, competitor_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze a topic against competitor activity.
        Returns saturation status and differentiation advice.
        """
        if not competitor_ids:
            return {
                "status": "no_competitors",
                "message": "No competitors tracked"
            }
            
        logger.info(f"Analyzing competitor saturation for topic '{topic}' against {len(competitor_ids)} rivals")
        
        # [AI UPGRADE] Use NLP Service for semantic matching
        from app.services.intelligence.nlp_service import nlp_service
        
        covered_by = []
        overlapping_videos = []
        threshold = 0.65  # Semantic similarity threshold
        
        for channel_id in competitor_ids:
            videos = self.rss_collector.get_recent_videos(channel_id, max_days=14)
            
            # Check each video title against the topic semantically
            video_titles = [v['title'] for v in videos]
            matches = nlp_service.batch_similarity(topic, video_titles)
            
            # Filter matches above threshold
            relevant_matches = [(title, score) for title, score in matches if score > threshold]
            
            if relevant_matches:
                # Found a semantic match!
                best_match_title, best_score = relevant_matches[0]
                channel_name = videos[0]['channel_title']  # Assume all videos from same channel have same title in RSS? No, channel_title is in video dict
                
                logger.info(f"🎯 Semantic Match: '{topic}' ~= '{best_match_title}' ({best_score:.2f}) by {channel_name}")
                
                covered_by.append(channel_name)
                # Find the full video object for the best match
                for v in videos:
                    if v['title'] == best_match_title:
                        v['similarity_score'] = best_score
                        overlapping_videos.append(v)
                        break
        
        is_saturated = len(covered_by) > 0
        covered_by = list(set(covered_by)) # Deduplicate
        
        advice = self._generate_advice(topic, is_saturated, covered_by)
        
        return {
            "status": "analyzed_ai",
            "is_saturated": is_saturated,
            "competitor_coverage": covered_by,
            "videos": overlapping_videos,
            "differentiation_advice": advice
        }
    
    def _generate_advice(self, topic: str, is_saturated: bool, covered_by: List[str]) -> str:
        """Generate specific advice based on saturation"""
        if not is_saturated:
            return f"🟢 **Green Light**: None of your tracked competitors have covered '{topic}' recently. This is a First Mover Advantage!"
            
        competitor_list = ", ".join(covered_by[:2])
        if len(covered_by) > 2:
            competitor_list += " and others"
            
        return f"🔴 **Differentiation Needed**: {competitor_list} recently posted about this. Don't cover the basics. Take a contrarian angle, do a deep dive they missed, or focus on a specific sub-niche aspect."
