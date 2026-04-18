import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock, patch

# Mock Qdrant and Embeddings before importing app
with patch('qdrant_client.QdrantClient'), patch('langchain_community.embeddings.SentenceTransformerEmbeddings'):
    from main import app

client = TestClient(app)

def test_health():
    """Positive Test: Check if Ingest API is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ingest-api"}

@patch('main.qdrant')
def test_invalid_upload(mock_qdrant):
    """Negative Test: Check if Ingest API handles missing file correctly"""
    response = client.post("/upload")
    assert response.status_code == 422 
