"""
Simple pytest configuration for the crypto sentiment agent tests.
"""

import pytest
import os
import tempfile
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
# from moto import mock_aws  # Will be enabled when moto is installed

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
        published_at=datetime(2024, 1, 1, 0, 0, 0),
        sentiment="bullish",
        confidence_score=0.85,
        tokens_mentioned=["BTC", "BITCOIN"]
    )
    test_db.add(article)
    test_db.commit()
    return article


# AWS mocking fixtures - will be enabled when moto is installed
# @pytest.fixture
# def mock_aws_services():
#     """Mock AWS services using Moto."""
#     with mock_aws():
#         yield
#
#
# @pytest.fixture
# def mock_s3_bucket(mock_aws_services):
#     """Create a mock S3 bucket with test PDF content."""
#     import boto3
#     from io import BytesIO
#
#     # Create S3 client
#     s3_client = boto3.client('s3', region_name='us-east-1')
#
#     # Create test bucket
#     bucket_name = 'test-crypto-news-bucket'
#     s3_client.create_bucket(Bucket=bucket_name)
#
#     # Create a mock PDF content
#     mock_pdf_content = b"Mock PDF content for testing"
#
#     # Upload test PDF
#     s3_client.put_object(
#         Bucket=bucket_name,
#         Key='test-article.pdf',
#         Body=mock_pdf_content,
#         ContentType='application/pdf'
#     )
#
#     return bucket_name
#
#
# @pytest.fixture
# def mock_bedrock_client(mock_aws_services):
#     """Mock Bedrock client for sentiment analysis."""
#     import boto3
#     from io import BytesIO
#
#     # Create Bedrock client
#     bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
#
#     # Mock the invoke_model method
#     def mock_invoke_model(*args, **kwargs):
#         return {
#             'body': BytesIO(b'{"content": [{"text": "{\\"sentiment\\": \\"bullish\\", \\"confidence\\": 0.85}"}]}'),
#             'contentType': 'application/json'
#         }
#
#     bedrock_client.invoke_model = mock_invoke_model
#     return bedrock_client
