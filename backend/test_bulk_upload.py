from fastapi.testclient import TestClient
from .main import app, get_current_active_superuser
from .models_db import User
import io

client = TestClient(app)

# Mock Admin Auth
async def mock_get_current_active_superuser():
    return User(id=1, email="admin@test.com", is_superuser=True)

app.dependency_overrides[get_current_active_superuser] = mock_get_current_active_superuser

def test_bulk_upload_csv():
    csv_content = """full_name,ssn,wages,federal_tax_withheld,state,tax_year,visa_type,days_present_2025,address,city,zip_code,country_of_residence,entry_date
Test Student 1,000-00-0001,5000,500,NY,2025,F1,365,123 St,NYC,10001,India,2020-01-01
Test Student 2,000-00-0002,10000,1000,CA,2025,J1,365,456 Ave,LA,90001,China,2021-01-01
"""
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    
    response = client.post("/api/admin/bulk-upload", files=files)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=" in response.headers["content-disposition"]

def test_bulk_upload_invalid_file():
    files = {'file': ('test.txt', 'some text', 'text/plain')}
    response = client.post("/api/admin/bulk-upload", files=files)
    assert response.status_code == 400
