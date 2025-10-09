"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.models import NewsArticle


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


def test_get_news_endpoint(test_client, sample_news_article):
    """Test getting news articles."""
    response = test_client.get("/api/news/")

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total_count" in data
    assert data["total_count"] == 1
    assert len(data["articles"]) == 1
    assert data["articles"][0]["title"] == "Bitcoin Price Surges to New Highs"


def test_get_sentiment_endpoint(test_client, sample_news_article):
    """Test getting sentiment analysis."""
    response = test_client.get("/api/sentiment/")

    assert response.status_code == 200
    data = response.json()
    assert "overall_sentiment" in data
    assert "sentiment_distribution" in data
    assert data["overall_sentiment"] == "bullish"
    assert data["sentiment_distribution"]["bullish"] == 1


def test_process_s3_endpoint(test_client):
    """Test S3 processing endpoint."""
    # Mock the entire S3Processor class to avoid AWS dependencies
    with patch('src.services.s3_processor.S3Processor') as mock_processor_class:
        mock_processor = MagicMock()
        mock_processor.process_all_articles.return_value = []
        mock_processor_class.return_value = mock_processor

        response = test_client.post("/api/process/s3/")

        # Should succeed with mocked processor
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "S3 PDFs processed successfully"


def test_fetch_live_news_endpoint(test_client):
    """Test fetch live news endpoint."""
    # Mock the CoinGecko service to avoid API dependencies
    with patch('src.services.coingecko_service.fetch_latest_news') as mock_fetch:
        mock_fetch.return_value = None  # No return value expected

        response = test_client.post("/api/fetch/live/")

        # Should succeed with mocked service
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Live news fetched successfully"


def test_analyze_sentiment_endpoint(test_client):
    """Test analyze sentiment endpoint."""
    # Mock the sentiment analyzer to avoid AWS Bedrock dependencies
    with patch('src.services.sentiment_analyzer.analyze_all_articles') as mock_analyze:
        mock_analyze.return_value = None  # No return value expected

        response = test_client.post("/api/analyze/sentiment/")

        # Should succeed with mocked analyzer
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sentiment analysis completed successfully"
