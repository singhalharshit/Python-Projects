from typing import Dict
from datetime import datetime
from models import User, UserCreate

_users: Dict[int, User] = {}
_email_index: Dict[str, int] = {}
_current_id = 0


def create_user(user_data: UserCreate) -> User:
    global _current_id

    # ✅ Email uniqueness check
    if user_data.email in _email_index:
        raise ValueError("Email already exists")

    _current_id += 1

    user = User(
        id=_current_id,
        username=user_data.username,
        email=user_data.email,
        is_active=True,
        created_at=datetime.utcnow().isoformat()
    )

    _users[user.id] = user
    _email_index[user.email] = user.id

    return user

def all_active_user(is_active):
    