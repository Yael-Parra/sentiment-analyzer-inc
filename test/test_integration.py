# tests/test_integration.py
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_predict_endpoint_mocked():
    response = client.post("/predict", json={"url": "https://fake.youtube.url/test"})
    assert response.status_code == 200
    data = response.json()
    assert "sentiment_summary" in data
    assert "toxicity_score" in data
