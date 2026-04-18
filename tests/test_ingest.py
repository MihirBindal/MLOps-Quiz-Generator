import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app
except ImportError:
    from ingest.main import app

client = TestClient(app)

def test_health():
    """Positive Test: Check if Ingest API is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ingest-api"}

def test_invalid_upload():
    """Negative Test: Check if Ingest API handles missing file correctly"""
    response = client.post("/upload")
    assert response.status_code == 422 
