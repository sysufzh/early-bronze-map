"""Create the initial admin user. Run: python seed_admin.py <username> <password>"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.auth import hash_password
from app.models import User


def seed_admin(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.is_admin = True
            user.hashed_password = hash_password(password)
            print(f"User '{username}' updated to admin with new password.")
        else:
            user = User(
                username=username,
                hashed_password=hash_password(password),
                is_admin=True,
            )
            db.add(user)
            print(f"Admin user '{username}' created.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python seed_admin.py <username> <password>")
        sys.exit(1)
    seed_admin(sys.argv[1], sys.argv[2])
