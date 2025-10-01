"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.models import NewsArticle


@pytest.fixture
def test_client():
    """Create a test client."""
    from src.main import app
    return TestClient(app)


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Crypto News & Sentiment Agent"
    assert data["version"] == "0.1.0"


def test_health_endpoint(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_news_endpoint(test_client):
    """Test getting news articles."""
    response = test_client.get("/api/news/")

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total_count" in data


def test_get_sentiment_endpoint(test_client):
    """Test getting sentiment analysis."""
    response = test_client.get("/api/sentiment/")

    assert response.status_code == 200
    data = response.json()
    assert "overall_sentiment" in data
    assert "sentiment_distribution" in data


def test_process_s3_endpoint(test_client):
    """Test S3 processing endpoint."""
    with patch('src.services.s3_processor.process_s3_pdfs') as mock_process:
        response = test_client.post("/api/process/s3/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "S3 PDFs processed successfully"
        mock_process.assert_called_once()


def test_fetch_live_news_endpoint(test_client):
    """Test fetch live news endpoint."""
    with patch('src.services.coingecko_service.fetch_latest_news') as mock_fetch:
        response = test_client.post("/api/fetch/live/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Live news fetched successfully"
        mock_fetch.assert_called_once()


def test_analyze_sentiment_endpoint(test_client):
    """Test analyze sentiment endpoint."""
    with patch('src.services.sentiment_analyzer.analyze_all_articles') as mock_analyze:
        response = test_client.post("/api/analyze/sentiment/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sentiment analysis completed successfully"
        mock_analyze.assert_called_once()
