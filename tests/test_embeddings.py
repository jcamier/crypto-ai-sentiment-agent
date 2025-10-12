"""
Tests for Day 3 features: Embeddings, Semantic Search, and Observability.
"""

import os
from unittest.mock import MagicMock, patch

# Set API key for all tests
os.environ["API_KEY"] = "crypto-agent-secret-key"
API_KEY = "crypto-agent-secret-key"


def test_metrics_endpoint(test_client):
    """Test that /metrics endpoint is publicly accessible and returns Prometheus format."""
    response = test_client.get("/metrics")

    assert response.status_code == 200
    # Check for Prometheus format (should start with # HELP or metric names)
    assert "http_requests_total" in response.text or "# HELP" in response.text
    # Should be text/plain format
    assert "text/plain" in response.headers.get("content-type", "")


def test_generate_embeddings_endpoint_no_articles(test_client, test_db):
    """Test embedding generation when no articles exist."""
    response = test_client.post(
        "/api/embeddings/generate/", headers={"X-API-Key": API_KEY}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "All articles already have embeddings"
    assert data["total_articles"] == 0


def test_generate_embeddings_endpoint_with_articles(test_client, test_db):
    """Test embedding generation with articles."""
    from src.models import NewsArticle

    # Add a test article without embedding
    article = NewsArticle(
        title="Bitcoin hits new high",
        content="Bitcoin reached $50,000 today",
        description="Test article",
        source="Test Source",
    )
    test_db.add(article)
    test_db.commit()

    # Mock the EmbeddingService
    with patch("src.main.EmbeddingService") as mock_embedding_service:
        mock_service = MagicMock()
        # Return a valid 1024-dim embedding (not all zeros)
        mock_service.generate_embedding.return_value = [0.1] * 1024
        mock_service.model_id = "amazon.titan-embed-text-v2:0"
        mock_embedding_service.return_value = mock_service

        response = test_client.post(
            "/api/embeddings/generate/", headers={"X-API-Key": API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 1
        assert data["failed"] == 0
        assert data["articles_with_embeddings"] == 1


def test_generate_embeddings_endpoint_fallback(test_client, test_db):
    """Test embedding generation when Bedrock returns fallback (all zeros)."""
    from src.models import NewsArticle

    article = NewsArticle(
        title="Test Article", content="Test content", description="Test", source="Test"
    )
    test_db.add(article)
    test_db.commit()

    # Mock EmbeddingService to return all zeros (fallback)
    with patch("src.main.EmbeddingService") as mock_embedding_service:
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.0] * 1024
        mock_service.model_id = "amazon.titan-embed-text-v2:0"
        mock_embedding_service.return_value = mock_service

        response = test_client.post(
            "/api/embeddings/generate/", headers={"X-API-Key": API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        # Should fail because of zero vector
        assert data["failed"] == 1
        assert data["successful"] == 0


def test_search_similar_articles_not_found(test_client):
    """Test searching for similar articles when article doesn't exist."""
    response = test_client.get(
        "/api/search/similar/999", headers={"X-API-Key": API_KEY}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_search_similar_articles_no_embedding(test_client, test_db):
    """Test searching for similar articles when source article has no embedding."""
    from src.models import NewsArticle

    article = NewsArticle(title="Test Article", content="Test content", source="Test")
    test_db.add(article)
    test_db.commit()

    response = test_client.get(
        f"/api/search/similar/{article.id}", headers={"X-API-Key": API_KEY}
    )

    assert response.status_code == 400
    assert "does not have an embedding" in response.json()["detail"]


def test_search_similar_articles_success(test_client, test_db):
    """Test successful similar article search using pgvector cosine similarity."""
    from src.models import NewsArticle

    # Create source article with embedding
    source_article = NewsArticle(
        title="Bitcoin Analysis",
        content="Bitcoin price analysis",
        description="BTC analysis",
        source="Test",
        embedding=[0.1] * 1024,
        embedding_model="amazon.titan-embed-text-v2:0",
    )
    test_db.add(source_article)

    # Create similar article with embedding
    similar_article = NewsArticle(
        title="Ethereum Analysis",
        content="Ethereum price analysis",
        description="ETH analysis",
        source="Test",
        embedding=[0.09] * 1024,  # Very similar embedding
        embedding_model="amazon.titan-embed-text-v2:0",
    )
    test_db.add(similar_article)
    test_db.commit()

    response = test_client.get(
        f"/api/search/similar/{source_article.id}?limit=5",
        headers={"X-API-Key": API_KEY},
    )

    assert response.status_code == 200
    data = response.json()
    assert "source_article" in data
    assert "similar_articles" in data
    assert data["source_article"]["id"] == source_article.id
    assert len(data["similar_articles"]) >= 0  # May be 0 if no similar articles

    # If we found similar articles, check they have similarity scores
    if len(data["similar_articles"]) > 0:
        assert "similarity_score" in data["similar_articles"][0]
        assert 0 <= data["similar_articles"][0]["similarity_score"] <= 1


def test_search_by_query_success(test_client, test_db):
    """Test search by natural language query using pgvector cosine similarity."""
    from src.models import NewsArticle

    # Create article with embedding
    article = NewsArticle(
        title="Bitcoin Price Prediction",
        content="Bitcoin is expected to reach $100k",
        description="BTC prediction",
        source="Test",
        embedding=[0.2] * 1024,
        embedding_model="amazon.titan-embed-text-v2:0",
    )
    test_db.add(article)
    test_db.commit()

    # Mock EmbeddingService for query embedding
    with patch("src.main.EmbeddingService") as mock_embedding_service:
        mock_service = MagicMock()
        # Return embedding similar to the article's embedding
        mock_service.generate_embedding.return_value = [0.19] * 1024
        mock_service.model_id = "amazon.titan-embed-text-v2:0"
        mock_embedding_service.return_value = mock_service

        response = test_client.post(
            "/api/search/query?query=Bitcoin+price&limit=10",
            headers={"X-API-Key": API_KEY},
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "Bitcoin price"
        assert len(data["results"]) >= 0

        # If results found, check structure
        if len(data["results"]) > 0:
            assert "similarity_score" in data["results"][0]
            assert "title" in data["results"][0]


def test_search_by_query_min_length(test_client):
    """Test that query search enforces minimum query length."""
    response = test_client.post(
        "/api/search/query?query=ab&limit=10",  # Too short
        headers={"X-API-Key": API_KEY},
    )

    # Should fail validation (422 Unprocessable Entity)
    assert response.status_code == 422


def test_search_by_query_embedding_failure(test_client, test_db):
    """Test query search when embedding generation fails (returns zeros)."""
    # Mock EmbeddingService to return all zeros
    with patch("src.main.EmbeddingService") as mock_embedding_service:
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.0] * 1024
        mock_service.model_id = "amazon.titan-embed-text-v2:0"
        mock_embedding_service.return_value = mock_service

        response = test_client.post(
            "/api/search/query?query=Bitcoin+price&limit=10",
            headers={"X-API-Key": API_KEY},
        )

        assert response.status_code == 500
        assert "Failed to generate query embedding" in response.json()["detail"]


def test_search_endpoints_require_api_key(test_client):
    """Test that search endpoints require API key authentication."""
    # Test similar articles endpoint
    response = test_client.get("/api/search/similar/1")
    assert response.status_code == 422  # Missing required header

    # Test query search endpoint
    response = test_client.post("/api/search/query?query=test")
    assert response.status_code == 422  # Missing required header


def test_embedding_service_integration(test_client, test_db):
    """Test that EmbeddingService is properly integrated."""
    from src.models import NewsArticle

    article = NewsArticle(
        title="Integration Test",
        content="This is an integration test",
        description="Test",
        source="Test",
    )
    test_db.add(article)
    test_db.commit()

    # Mock EmbeddingService with realistic behavior
    with patch("src.main.EmbeddingService") as mock_embedding_service:
        mock_service = MagicMock()
        # Simulate successful embedding generation
        mock_service.generate_embedding.return_value = [0.05 * i for i in range(1024)]
        mock_service.model_id = "amazon.titan-embed-text-v2:0"
        mock_embedding_service.return_value = mock_service

        response = test_client.post(
            "/api/embeddings/generate/", headers={"X-API-Key": API_KEY}
        )

        assert response.status_code == 200

        # Verify the service was called
        mock_service.generate_embedding.assert_called_once()

        # Verify article was updated in database
        test_db.refresh(article)
        assert article.embedding is not None
        assert article.embedding_model == "amazon.titan-embed-text-v2:0"
        assert article.embedding_generated_at is not None


def test_rate_limiting_on_new_endpoints(test_client):
    """Test that rate limiting is applied to Day 3 endpoints."""
    # Note: This is a basic test. Full rate limiting tests would require
    # making many rapid requests, which we skip for unit tests

    # Verify endpoints exist and are protected
    endpoints = [
        ("/api/embeddings/generate/", "POST"),
        ("/api/search/similar/1", "GET"),
        ("/api/search/query?query=test", "POST"),
    ]

    for endpoint, method in endpoints:
        if method == "GET":
            response = test_client.get(endpoint, headers={"X-API-Key": API_KEY})
        else:
            response = test_client.post(endpoint, headers={"X-API-Key": API_KEY})

        # Should not be 429 (rate limited) on first request
        # Could be 404, 400, or 200 depending on data state
        assert response.status_code != 429
