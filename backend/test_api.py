from fastapi.testclient import TestClient
import pytest

def test_register_user(client: TestClient):
    response = client.post(
        "/api/register",
        json={"email": "testuser@example.com", "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_login_user(client: TestClient):
    # Register first
    client.post(
        "/api/register",
        json={"email": "testuser@example.com", "password": "password123", "full_name": "Test User"}
    )
    response = client.post(
        "/api/token",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

def test_read_users_me(client: TestClient):
    token = test_login_user(client)
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"

def test_create_tax_return(client: TestClient):
    token = test_login_user(client)
    tax_data = {
        "tax_year": 2025,
        "full_name": "Test User",
        "ssn": "000-00-0000",
        "wages": 50000,
        "federal_tax_withheld": 5000,
        "address": "123 Main St",
        "city": "City",
        "state": "NY",
        "zip_code": "10001",
        "country_of_residence": "India",
        "visa_type": "F1"
    }
    response = client.post(
        "/api/tax-returns",
        json=tax_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_get_tax_return(client: TestClient):
    token = test_login_user(client)
    tax_data = {
        "tax_year": 2025,
        "full_name": "Test User",
        "ssn": "000-00-0000",
        "wages": 50000,
        "federal_tax_withheld": 5000,
        "address": "123 Main St",
        "city": "City",
        "state": "NY",
        "zip_code": "10001",
        "country_of_residence": "India",
        "visa_type": "F1"
    }
    client.post(
        "/api/tax-returns",
        json=tax_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.get(
        "/api/tax-returns/2025",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["wages"] == 50000
    assert data["full_name"] == "Test User"
