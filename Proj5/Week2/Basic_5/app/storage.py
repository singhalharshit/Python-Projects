#storage.py

from typing import Dict
from datetime import datetime
from models import User, UserCreate,UserUpdate

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


def all_active_user(is_active:bool | None=None):
    user = list(_users.values())
    if is_active is None:
        return user
    return [i for i in user if i.is_active==is_active]


def get_user_by_id(user_id: int) -> User | None:
    return _users.get(user_id)


def update_user(user_id: int, user_data: UserUpdate) -> User | None:
    if user_id not in _users:
        return None

    user = _users[user_id]

    # Handle email update with uniqueness check
    if user_data.email:
        if (
            user_data.email in _email_index
            and _email_index[user_data.email] != user_id
        ):
            raise ValueError("Email already exists")

        # update email index
        del _email_index[user.email]
        _email_index[user_data.email] = user_id
        user.email = user_data.email

    if user_data.username:
        user.username = user_data.username

    _users[user_id] = user
    return user


def soft_delete(user_id:int):
    if user_id not in _users:
        return None
    else:
        _users[user_id].is_active=False
    return _users[user_id]