"""
Google Trends data collector using pytrends (unofficial API)
No API key required - completely free!
"""
from pytrends.request import TrendReq
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter
import logging
from app.core.resilience import with_circuit_breaker

logger = logging.getLogger(__name__)


class GoogleTrendsCollector:
    """Collects trend signals from Google Trends"""
    
    def __init__(self):
        # Initialize pytrends with language and timezone
        self.pytrends = TrendReq(hl='en-US', tz=360)
    
    @with_circuit_breaker("google_trends")
    def collect_niche_signals(
        self,
        keywords: List[str],
        niche: str,
        geo: str = "",  # Empty for worldwide, or use 'US', 'GB', etc.
        timeframe: str = 'now 7-d'  # Last 7 days
    ) -> Dict[str, Any]:
        """
        Collect trending signals from Google Trends
        
        Args:
            keywords: Search keywords for the niche (max 5 at a time)
            niche: Niche identifier
            geo: Geographic location (empty for worldwide)
            timeframe: Time range for trends (default: last 7 days)
        
        Returns:
            Dictionary with trending topics and interest metrics
        """
        logger.info(f"Collecting Google Trends signals for {niche} with keywords: {keywords}")
        
        # Google Trends allows max 5 keywords at a time
        keywords = keywords[:5]
        
        try:
            # Build payload for interest over time
            self.pytrends.build_payload(
                keywords,
                cat=0,
                timeframe=timeframe,
                geo=geo,
                gprop=''
            )
            
            # Get interest over time
            interest_over_time_df = self.pytrends.interest_over_time()
            
            # Get related queries (rising and top)
            related_queries = self.pytrends.related_queries()
            
            # Get trending searches (daily trends)
            try:
                trending_searches = self.pytrends.trending_searches(pn='united_states')
                trending_now = trending_searches[0].head(10).tolist() if not trending_searches.empty else []
            except Exception as e:
                logger.warning(f"Could not fetch trending searches: {e}")
                trending_now = []
            
            # Analyze interest over time
            trending_topics = self._analyze_interest_trends(
                interest_over_time_df,
                keywords,
                related_queries
            )
            
            # Calculate momentum metrics
            momentum_metrics = self._calculate_momentum_metrics(interest_over_time_df, keywords)
            
            return {
                "source": "google_trends",
                "niche": niche,
                "trending_topics": trending_topics,
                "momentum_metrics": momentum_metrics,
                "trending_now": trending_now,
                "keywords": keywords,
                "timestamp": datetime.utcnow(),
                "timeframe": timeframe,
                "geo": geo or "worldwide"
            }
            
        except Exception as e:
            logger.error(f"Error collecting Google Trends data: {e}")
            raise
    
    def _analyze_interest_trends(
        self,
        interest_df,
        keywords: List[str],
        related_queries: Dict
    ) -> List[Dict[str, Any]]:
        """Analyze interest trends and identify rising topics"""
        
        trending = []
        
        if interest_df.empty:
            return trending
        
        for keyword in keywords:
            if keyword not in interest_df.columns:
                continue
            
            # Get interest values
            values = interest_df[keyword].values
            
            # Calculate trend direction (rising, stable, falling)
            if len(values) >= 2:
                recent_avg = values[-3:].mean() if len(values) >= 3 else values[-1]
                older_avg = values[:-3].mean() if len(values) >= 3 else values[0]
                
                # Momentum score based on growth
                if older_avg > 0:
                    growth_rate = (recent_avg - older_avg) / older_avg
                else:
                    growth_rate = 1.0 if recent_avg > 0 else 0.0
                
                # Determine trend direction
                if growth_rate > 0.2:
                    trend_direction = "rising"
                    momentum_score = min(growth_rate, 1.0)
                elif growth_rate < -0.2:
                    trend_direction = "falling"
                    momentum_score = 0.0
                else:
                    trend_direction = "stable"
                    momentum_score = 0.5
                
                # Get rising related queries
                rising_queries = []
                if keyword in related_queries and related_queries[keyword]['rising'] is not None:
                    rising_df = related_queries[keyword]['rising']
                    if not rising_df.empty:
                        rising_queries = rising_df['query'].head(5).tolist()
                
                trending.append({
                    "topic": keyword,
                    "trend_direction": trend_direction,
                    "momentum_score": momentum_score,
                    "current_interest": int(recent_avg),
                    "avg_interest": int(values.mean()),
                    "peak_interest": int(values.max()),
                    "growth_rate": round(growth_rate * 100, 2),
                    "rising_related_queries": rising_queries
                })
        
        # Sort by momentum score
        trending.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        return trending
    
    def _calculate_momentum_metrics(self, interest_df, keywords: List[str]) -> Dict[str, Any]:
        """Calculate overall momentum metrics"""
        
        if interest_df.empty:
            return {
                "overall_momentum": 0.0,
                "avg_interest": 0,
                "peak_interest": 0,
                "trend_velocity": 0.0
            }
        
        # Calculate overall metrics across all keywords
        all_values = []
        for keyword in keywords:
            if keyword in interest_df.columns:
                all_values.extend(interest_df[keyword].values)
        
        if not all_values:
            return {
                "overall_momentum": 0.0,
                "avg_interest": 0,
                "peak_interest": 0,
                "trend_velocity": 0.0
            }
        
        avg_interest = sum(all_values) / len(all_values)
        peak_interest = max(all_values)
        
        # Calculate velocity (rate of change)
        recent_values = all_values[-len(keywords)*3:] if len(all_values) >= len(keywords)*3 else all_values
        older_values = all_values[:len(keywords)*3] if len(all_values) >= len(keywords)*3 else all_values
        
        recent_avg = sum(recent_values) / len(recent_values) if recent_values else 0
        older_avg = sum(older_values) / len(older_values) if older_values else 0
        
        if older_avg > 0:
            velocity = (recent_avg - older_avg) / older_avg
        else:
            velocity = 1.0 if recent_avg > 0 else 0.0
        
        # Overall momentum (0-1 scale)
        momentum = min((avg_interest / 100) * 0.5 + min(abs(velocity), 1.0) * 0.5, 1.0)
        
        return {
            "overall_momentum": round(momentum, 3),
            "avg_interest": int(avg_interest),
            "peak_interest": int(peak_interest),
            "trend_velocity": round(velocity, 3)
        }
    
    @with_circuit_breaker("google_trends")
    def get_trending_searches(self, country: str = 'united_states') -> List[str]:
        """
        Get current trending searches for a specific country
        
        Args:
            country: Country name (e.g., 'united_states', 'united_kingdom')
        
        Returns:
            List of trending search terms
        """
        try:
            trending_df = self.pytrends.trending_searches(pn=country)
            return trending_df[0].head(20).tolist() if not trending_df.empty else []
        except Exception as e:
            logger.error(f"Error fetching trending searches: {e}")
            return []
    
    @with_circuit_breaker("google_trends")
    def get_suggestions(self, keyword: str) -> List[str]:
        """
        Get keyword suggestions from Google Trends
        
        Args:
            keyword: Base keyword to get suggestions for
        
        Returns:
            List of suggested keywords
        """
        try:
            suggestions = self.pytrends.suggestions(keyword=keyword)
            return [s['title'] for s in suggestions] if suggestions else []
        except Exception as e:
            logger.error(f"Error fetching suggestions: {e}")
            return []
