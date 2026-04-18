import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add service directories to path so we can import apps
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ingest"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "generate"))

# Import apps (suppressing heavy init if possible, but TestClient handles it)
try:
    from ingest.main import app as ingest_app
    from generate.main import app as generate_app
except ImportError:
    # Fallback for different directory structures in CI
    from main import app as ingest_app
    from main import app as generate_app

ingest_client = TestClient(ingest_app)
generate_client = TestClient(generate_app)

# --- POSITIVE TESTS ---

def test_ingest_health():
    """Check if Ingest API is healthy"""
    response = ingest_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ingest-api"}

def test_generate_health():
    """Check if Generate API is healthy"""
    response = generate_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "generate-api"}

# --- NEGATIVE TESTS ---

def test_ingest_invalid_upload():
    """Check if Ingest API handles missing file correctly"""
    # Sending no file to a required file endpoint
    response = ingest_client.post("/upload")
    assert response.status_code == 422 # Unprocessable Entity (FastAPI default)

def test_generate_empty_payload():
    """Check if Generate API handles empty JSON correctly"""
    response = generate_client.post("/generate", json={})
    assert response.status_code == 422 # Validation Error for missing fields
