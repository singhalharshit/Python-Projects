from sqlalchemy.orm import Session

from app.services.intelligence.realtime_preference_learner import RealTimePreferenceLearner
from app.services.intelligence.vector_store import VectorStore

class CompetitorDiscoveryV2:
    def __init__(self, vector_store, preference_learner):
        self.vector_store = vector_store
        self.preference_learner = preference_learner

    def discover(self, user_id: str, limit: int = 50):
        user_vector = self.preference_learner.get_or_create_user_vector(user_id)

        results = self.vector_store.similarity_search(
            query_vector=user_vector,
            top_k=limit * 2
        )

        # Filter out rejected competitors
        rejected = self.vector_store.get_rejected_ids(user_id)

        filtered = [
            r for r in results if r["id"] not in rejected
        ]

        return filtered[:limit]
