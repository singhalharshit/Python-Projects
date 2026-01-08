from database import SessionLocal
from models import User


db=SessionLocal()

try:
    users= db.query(User).all()
    print(f'Found {len(users)} Users')
    
    for user in users:
        print(
            f"id={user.id}, "
            f"email={user.email}, "
            f"role={user.role}, "
            f"active={user.is_active}"
        )
finally:
    db.close()