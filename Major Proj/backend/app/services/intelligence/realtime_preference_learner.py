import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user_preference_vector import UserPreferenceVector
from app.models.competitor_feedback import CompetitorFeedback
from app.services.intelligence.embedding_service import EmbeddingService


LEARNING_RATE_POSITIVE = 0.15
LEARNING_RATE_NEGATIVE = 0.08
VECTOR_NORM_CLIP = 5.0


class RealTimePreferenceLearner:
    def __init__(self, db: Session, embedding_service):
        self.db = db
        self.embedding_service = embedding_service

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        if norm > VECTOR_NORM_CLIP:
            return v / norm * VECTOR_NORM_CLIP
        return v

    def get_or_create_user_vector(self, user_id: str) -> np.ndarray:
        record = self.db.execute("SELECT vector FROM user_preference_vectors WHERE user_id = :uid",
            {"uid": user_id}
        ).fetchone()

        if record:
            return np.array(record[0])

        # Cold start = user's own content embedding
        base_vector = self.embedding_service.get_creator_embedding(user_id)

        self.db.execute(
            """
            INSERT INTO user_preference_vectors (user_id, vector)
            VALUES (:uid, :vector)
            """,
            {"uid": user_id, "vector": base_vector.tolist()}
        )
        self.db.commit()

        return np.array(base_vector)

    def update(self, user_id: str, competitor_id: str, action: str):
        user_vector = self.get_or_create_user_vector(user_id)
        competitor_vector = self.embedding_service.get_creator_embedding(competitor_id)

        competitor_vector = np.array(competitor_vector)

        similarity = float(
            np.dot(user_vector, competitor_vector)
            / (np.linalg.norm(user_vector) * np.linalg.norm(competitor_vector))
        )

        if action == "accept":
            delta = LEARNING_RATE_POSITIVE * competitor_vector
        elif action == "reject":
            delta = -LEARNING_RATE_NEGATIVE * competitor_vector
        else:
            raise ValueError("Invalid action")

        new_vector = self._normalize(user_vector + delta)

        # Persist
        self.db.execute(
            """
            UPDATE user_preference_vectors
            SET vector = :vector, updated_at = :now
            WHERE user_id = :uid
            """,
            {
                "uid": user_id,
                "vector": new_vector.tolist(),
                "now": datetime.utcnow()
            }
        )

        self.db.execute(
            """
            INSERT INTO competitor_feedback
            (id, user_id, competitor_id, action, similarity_score)
            VALUES (gen_random_uuid(), :uid, :cid, :action, :sim)
            """,
            {
                "uid": user_id,
                "cid": competitor_id,
                "action": action,
                "sim": similarity
            }
        )

        self.db.commit()

        return {
            "updated": True,
            "similarity": similarity
        }
