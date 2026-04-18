import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock, patch

# Add local directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Mock Qdrant and LLM before importing app to avoid initialization errors
with patch('qdrant_client.QdrantClient'), patch('langchain_google_genai.ChatGoogleGenerativeAI'):
    from main import app

client = TestClient(app)

def test_health():
    """Positive Test: Check if Generate API is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "generate-api"}

def test_invalid_payload():
    """Negative Test: Check if Generate API handles invalid data types correctly"""
    # Sending a string instead of a JSON object will trigger a 422 before LLM/Qdrant logic
    response = client.post("/generate", content="not-a-json")
    assert response.status_code == 422
