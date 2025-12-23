from typing import Dict,Optional
from datetime import datetime
from models import User, UserCreate
from fastapi import HTTPException

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
    return [i for i in user if i.is_active==is_active]


def user_list(id:int):
    if id in list(_users.keys()):
        return _users[id]
    raise HTTPException(status_code=404,detail="User Not Found")


def update_user