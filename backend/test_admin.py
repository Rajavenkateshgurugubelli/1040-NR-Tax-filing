from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .main import app
from .database import Base, get_db
from .models_db import User
from .auth import get_password_hash
import pytest

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def create_test_admin():
    db = TestingSessionLocal()
    hashed_password = get_password_hash("admin123")
    admin = User(email="admin@test.com", password_hash=hashed_password, full_name="Admin", is_superuser=True)
    db.add(admin)
    db.commit()
    db.close()

def create_test_user():
    db = TestingSessionLocal()
    hashed_password = get_password_hash("user123")
    user = User(email="user@test.com", password_hash=hashed_password, full_name="User", is_superuser=False)
    db.add(user)
    db.commit()
    db.close()

def test_admin_access():
    create_test_admin()
    create_test_user()
    
    # Login as Admin
    response = client.post("/api/token", data={"username": "admin@test.com", "password": "admin123"})
    token = response.json()["access_token"]
    
    # Access Admin Endpoint
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2

def test_user_access_denied():
    # Login as User
    response = client.post("/api/token", data={"username": "user@test.com", "password": "user123"})
    token = response.json()["access_token"]
    
    # Access Admin Endpoint
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
