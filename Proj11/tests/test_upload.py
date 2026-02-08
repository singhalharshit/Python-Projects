from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_unauthorized():
    response = client.post("/files/upload")
    assert response.status_code == 401
