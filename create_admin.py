from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models_db import User
from backend.auth import get_password_hash
import sys

SQLALCHEMY_DATABASE_URL = "sqlite:///./tax_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def create_admin(email, password):
    db = SessionLocal()
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User {email} already exists.")
        # Always update password and superuser status
        user.password_hash = get_password_hash(password)
        user.is_superuser = True
        db.commit()
        print(f"User {email} updated (password reset & promoted to superuser).")
        return

    hashed_password = get_password_hash(password)
    db_user = User(email=email, password_hash=hashed_password, full_name="Admin User", is_superuser=True)
    db.add(db_user)
    db.commit()
    print(f"Superuser {email} created successfully.")
    db.close()

if __name__ == "__main__":
    create_admin("admin@example.com", "admin123")
