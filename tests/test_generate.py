import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock, patch

# Mock Qdrant and LLM before importing app to avoid initialization errors
with patch('qdrant_client.QdrantClient'), patch('langchain_google_genai.ChatGoogleGenerativeAI'):
    from main import app

client = TestClient(app)

def test_health():
    """Positive Test: Check if Generate API is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "generate-api"}

@patch('main.qdrant')
def test_empty_payload(mock_qdrant):
    """Negative Test: Check if Generate API handles empty JSON correctly"""
    # Mocking the query points to return nothing
    mock_qdrant.query_points.return_value = MagicMock()
    response = client.post("/generate", json={})
    # Since we send empty JSON, FastAPI validation should catch it before Qdrant anyway
    assert response.status_code == 422
