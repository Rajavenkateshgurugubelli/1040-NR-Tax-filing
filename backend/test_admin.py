from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from .models_db import User
from .auth import get_password_hash
import pytest

def create_test_admin(db: Session):
    hashed_password = get_password_hash("admin123")
    admin = User(email="admin@test.com", password_hash=hashed_password, full_name="Admin", is_superuser=True)
    db.add(admin)
    db.commit()

def create_test_user(db: Session):
    hashed_password = get_password_hash("user123")
    user = User(email="user@test.com", password_hash=hashed_password, full_name="User", is_superuser=False)
    db.add(user)
    db.commit()

def test_admin_access(client: TestClient, db_session: Session):
    create_test_admin(db_session)
    create_test_user(db_session)
    
    # Login as Admin
    response = client.post("/api/token", data={"username": "admin@test.com", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Access Admin Endpoint
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2

def test_user_access_denied(client: TestClient, db_session: Session):
    create_test_admin(db_session)
    create_test_user(db_session)
    
    # Login as User
    response = client.post("/api/token", data={"username": "user@test.com", "password": "user123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Access Admin Endpoint
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
