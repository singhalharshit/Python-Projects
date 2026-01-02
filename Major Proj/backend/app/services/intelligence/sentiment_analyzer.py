"""
Sentiment Analyzer - Detect vibe and mood from content
"""
import logging
from typing import List, Dict, Any
from collections import Counter
import numpy as np

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzes sentiment and vibe from content.
    
    Detects:
    - Sentiment (positive/negative/neutral)
    - Vibe (hype/critique/calm/controversy)
    - Confidence in detection
    
    Uses transformer-based sentiment analysis for accuracy.
    """
    
    def __init__(self):
        self.sentiment_pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize sentiment analysis model (lazy loading)"""
        try:
            from transformers import pipeline
            
            # Use RoBERTa model trained on social media text
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                max_length=512,
                truncation=True
            )
            logger.info("Sentiment analyzer initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize sentiment model: {e}")
            logger.warning("Falling back to rule-based sentiment analysis")
            self.sentiment_pipeline = None
    
    def analyze_vibe(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze overall vibe from multiple texts.
        
        Args:
            texts: List of text samples (titles, captions, comments, etc.)
        
        Returns:
            {
                'dominant_vibe': 'hype' | 'critique' | 'calm' | 'controversy' | 'mixed',
                'confidence': 0.0-1.0,
                'sentiment_distribution': {
                    'positive': 0.0-1.0,
                    'negative': 0.0-1.0,
                    'neutral': 0.0-1.0
                },
                'sample_count': int
            }
        """
        if not texts:
            return self._get_default_vibe()
        
        # Limit to 20 samples for performance
        sample_texts = texts[:20]
        
        if self.sentiment_pipeline:
            return self._analyze_with_model(sample_texts)
        else:
            return self._analyze_with_rules(sample_texts)
    
    def _analyze_with_model(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze using transformer model"""
        sentiments = []
        
        for text in texts:
            try:
                # Truncate long texts
                truncated_text = text[:512]
                result = self.sentiment_pipeline(truncated_text)[0]
                sentiments.append(result)
            except Exception as e:
                logger.warning(f"Sentiment analysis failed for text: {e}")
                continue
        
        if not sentiments:
            return self._get_default_vibe()
        
        # Aggregate sentiments
        sentiment_counts = Counter([s['label'] for s in sentiments])
        total = len(sentiments)
        
        # Calculate distribution
        positive_ratio = sentiment_counts.get('positive', 0) / total
        negative_ratio = sentiment_counts.get('negative', 0) / total
        neutral_ratio = sentiment_counts.get('neutral', 0) / total
        
        # Determine dominant vibe
        dominant_vibe, confidence = self._map_sentiment_to_vibe(
            positive_ratio,
            negative_ratio,
            neutral_ratio
        )
        
        return {
            'dominant_vibe': dominant_vibe,
            'confidence': confidence,
            'sentiment_distribution': {
                'positive': positive_ratio,
                'negative': negative_ratio,
                'neutral': neutral_ratio
            },
            'sample_count': total
        }
    
    def _analyze_with_rules(self, texts: List[str]) -> Dict[str, Any]:
        """Fallback rule-based sentiment analysis"""
        
        # Simple keyword-based approach
        positive_keywords = [
            'amazing', 'great', 'awesome', 'love', 'best', 'excellent',
            'fantastic', 'incredible', 'perfect', 'wonderful', '!', '🔥', '❤️'
        ]
        
        negative_keywords = [
            'bad', 'worst', 'terrible', 'hate', 'awful', 'horrible',
            'disappointing', 'failed', 'wrong', 'broken', 'issue', 'problem'
        ]
        
        neutral_keywords = [
            'update', 'new', 'release', 'announced', 'available',
            'launched', 'introduced', 'features'
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            pos_score = sum(1 for kw in positive_keywords if kw in text_lower)
            neg_score = sum(1 for kw in negative_keywords if kw in text_lower)
            neu_score = sum(1 for kw in neutral_keywords if kw in text_lower)
            
            if pos_score > neg_score and pos_score > neu_score:
                positive_count += 1
            elif neg_score > pos_score and neg_score > neu_score:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(texts)
        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        neutral_ratio = neutral_count / total
        
        dominant_vibe, confidence = self._map_sentiment_to_vibe(
            positive_ratio,
            negative_ratio,
            neutral_ratio
        )
        
        # Lower confidence for rule-based
        confidence *= 0.7
        
        return {
            'dominant_vibe': dominant_vibe,
            'confidence': confidence,
            'sentiment_distribution': {
                'positive': positive_ratio,
                'negative': negative_ratio,
                'neutral': neutral_ratio
            },
            'sample_count': total
        }
    
    def _map_sentiment_to_vibe(
        self,
        positive_ratio: float,
        negative_ratio: float,
        neutral_ratio: float
    ) -> tuple[str, float]:
        """
        Map sentiment distribution to vibe.
        
        Returns:
            (vibe, confidence)
        """
        
        # Hype: Predominantly positive
        if positive_ratio > 0.6:
            return 'hype', positive_ratio
        
        # Critique: Predominantly negative
        elif negative_ratio > 0.5:
            return 'critique', negative_ratio
        
        # Calm: Predominantly neutral
        elif neutral_ratio > 0.6:
            return 'calm', neutral_ratio
        
        # Controversy: Mixed positive and negative
        elif positive_ratio > 0.3 and negative_ratio > 0.3:
            controversy_strength = min(positive_ratio, negative_ratio) * 2
            return 'controversy', controversy_strength
        
        # Mixed: No clear pattern
        else:
            max_ratio = max(positive_ratio, negative_ratio, neutral_ratio)
            return 'mixed', max_ratio
    
    def _get_default_vibe(self) -> Dict[str, Any]:
        """Return default vibe when analysis fails"""
        return {
            'dominant_vibe': 'mixed',
            'confidence': 0.0,
            'sentiment_distribution': {
                'positive': 0.33,
                'negative': 0.33,
                'neutral': 0.34
            },
            'sample_count': 0
        }
    
    def get_vibe_description(self, vibe: str) -> str:
        """
        Get human-readable description of vibe.
        Used in calm explanations.
        """
        descriptions = {
            'hype': "enthusiastic and excited",
            'critique': "critical and analytical",
            'calm': "measured and informative",
            'controversy': "polarizing with mixed reactions",
            'mixed': "varied in tone"
        }
        
        return descriptions.get(vibe, "unclear")
    
    def should_avoid_vibe(self, vibe: str, creator_preference: str = None) -> bool:
        """
        Determine if this vibe should be avoided.
        
        Args:
            vibe: Detected vibe
            creator_preference: Creator's preferred vibe (optional)
        
        Returns:
            True if this vibe might not align with creator
        """
        # Controversy is generally risky
        if vibe == 'controversy':
            return True
        
        # If creator has preference, check alignment
        if creator_preference:
            return vibe != creator_preference
        
        return False


# Global instance (lazy loaded)
_sentiment_analyzer = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance"""
    global _sentiment_analyzer
    
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    
    return _sentiment_analyzer
