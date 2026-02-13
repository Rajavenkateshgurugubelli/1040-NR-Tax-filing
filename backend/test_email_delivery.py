
import pytest
from fastapi.testclient import TestClient
from backend.main import app, email_service, auth as auth_module
from backend.models import UserData
from backend import models_db

client = TestClient(app)

# Mock User Data
valid_user_data = {
    "full_name": "Test User",
    "ssn": "000-00-0000",
    "address": "123 Main St",
    "city": "City",
    "state": "NY",
    "zip_code": "10001",
    "wages": 50000.0,
    "federal_tax_withheld": 5000.0,
    "visa_type": "F1",
    "country_of_residence": "India",
    "email_delivery": "test@example.com"
}

# Mock current user dependency
def mock_get_current_user():
    return models_db.User(email="test@example.com", full_name="Test User", id=1)

app.dependency_overrides[auth_module.get_current_user] = mock_get_current_user

def test_email_endpoint_mock_success():
    """
    Test that the email endpoint returns 200 OK and "sends" the email
    when provided with an email address.
    """
    
    # We need to mock the email service to avoid actual network calls (although our service is already mocked if envs missing)
    # But explicitly mocking ensures we don't depend on env state
    original_send = email_service.send_tax_return_email
    email_service.send_tax_return_email = lambda to, pdf: True
    
    try:
        response = client.post(
            "/api/email-return?email=custom@example.com",
            json=valid_user_data
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "custom@example.com" in response.json()["message"]
        
    finally:
        email_service.send_tax_return_email = original_send

def test_download_package_refactor_success():
    """
    Verify that the refactored download_complete_package still works.
    """
    response = client.post(
        "/api/download-complete-package",
        json=valid_user_data
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Complete_Tax_Return_2025.pdf" in response.headers["content-disposition"]
