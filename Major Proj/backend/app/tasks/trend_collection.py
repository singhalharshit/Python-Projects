"""
Celery Tasks - Trend Collection
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.services.signals.live_signal_collector import LiveSignalCollector
from app.services.intelligence.vector_store import get_vector_store
from app.models.dynamic_niche import DynamicNiche

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.trend_collection.collect_trends_for_all_niches')
def collect_trends_for_all_niches():
    """
    Collect trends for all active niches.
    
    Runs every 2 hours via Celery Beat.
    """
    logger.info("Starting trend collection for all niches")
    
    db = next(get_db())
    
    try:
        # Get all active niches
        niches = db.query(DynamicNiche).all()
        
        if not niches:
            logger.warning("No niches found. Skipping trend collection.")
            return {
                'status': 'skipped',
                'reason': 'no_niches',
                'niches_processed': 0
            }
        
        logger.info(f"Collecting trends for {len(niches)} niches")
        
        # Initialize signal collector
        signal_collector = LiveSignalCollector(db)
        
        results = []
        
        for niche in niches:
            try:
                # Get niche centroid
                centroid = niche.get_centroid_vector()
                
                if centroid is None:
                    logger.warning(f"Niche {niche.label} has no centroid")
                    continue
                
                # Collect signals for this niche
                signals = signal_collector.collect_signals(
                    search_space=centroid,
                    radius=0.4,
                    max_signals=50
                )
                
                # Update niche momentum
                niche.signal_count_7d = len(signals)
                niche.momentum = min(len(signals) / 50.0, 1.0)
                
                db.commit()
                
                results.append({
                    'niche': niche.label,
                    'signals_collected': len(signals),
                    'momentum': niche.momentum
                })
                
                logger.info(
                    f"Collected {len(signals)} signals for niche '{niche.label}'"
                )
                
            except Exception as e:
                logger.error(f"Failed to collect for niche {niche.label}: {e}")
                continue
        
        logger.info(f"Trend collection complete: {len(results)} niches processed")
        
        return {
            'status': 'success',
            'niches_processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Trend collection failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.trend_collection.collect_trends_for_user')
def collect_trends_for_user(user_id: str):
    """
    Collect trends for a specific user's content space.
    
    Args:
        user_id: User ID
    """
    logger.info(f"Collecting trends for user {user_id}")
    
    db = next(get_db())
    
    try:
        # Get user's embedding from vector store
        vector_store = get_vector_store()
        creator_data = vector_store.get_creator_embedding(user_id)
        
        if creator_data is None:
            logger.error(f"User {user_id} not found in vector store")
            return {
                'status': 'error',
                'error': 'user_not_found'
            }
        
        # Collect signals
        signal_collector = LiveSignalCollector(db)
        signals = signal_collector.collect_signals(
            search_space=creator_data,
            radius=0.4,
            max_signals=50
        )
        
        logger.info(f"Collected {len(signals)} signals for user {user_id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'signals_collected': len(signals)
        }
        
    except Exception as e:
        logger.error(f"Failed to collect for user {user_id}: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()
