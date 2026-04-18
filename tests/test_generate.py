import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app
except ImportError:
    from generate.main import app

client = TestClient(app)

def test_health():
    """Positive Test: Check if Generate API is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "generate-api"}

def test_empty_payload():
    """Negative Test: Check if Generate API handles empty JSON correctly"""
    response = client.post("/generate", json={})
    assert response.status_code == 422
