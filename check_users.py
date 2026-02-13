from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./tax_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_users():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id, email, is_superuser FROM users"))
        users = result.fetchall()
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"User: {u.email} (Admin: {u.is_superuser})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
