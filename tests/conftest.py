"""
Simple pytest configuration for the crypto sentiment agent tests.
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test database URL before importing the app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DB_NAME"] = "test_crypto_news"
os.environ["DB_USER"] = "test_user"
os.environ["DB_PASS"] = "test_pass"

from src.database import Base, get_db
from src.main import app
from src.models import NewsArticle


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_db):
    """Create a test client with database dependency overridden."""
    return TestClient(app)


@pytest.fixture
def sample_news_article(test_db):
    """Create a sample news article for testing."""
    article = NewsArticle(
        title="Bitcoin Price Surges to New Highs",
        content="Bitcoin has reached new all-time highs as institutional adoption continues to grow...",
        source="CoinDesk",
        url="https://example.com/bitcoin-surge",
        published_at="2024-01-01T00:00:00Z",
        sentiment="bullish",
        confidence_score=0.85,
        tokens_mentioned=["BTC", "BITCOIN"]
    )
    test_db.add(article)
    test_db.commit()
    return article
