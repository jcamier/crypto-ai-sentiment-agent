"""
Pytest configuration for the crypto sentiment agent tests.

Uses PostgreSQL with pgvector for tests to match production environment.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# from moto import mock_aws  # Will be enabled when moto is installed

# Set test database URL
# Use the same database as development, but we'll clean it up before/after each test
# Read database credentials from environment (set in docker-compose.yml or GitHub Actions)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "crypto_news")

# GitHub Actions provides DATABASE_URL, otherwise construct it
# If DATABASE_URL is provided, use it (GitHub Actions: localhost, Docker: db)
if "DATABASE_URL" in os.environ:
    TEST_DATABASE_URL = os.environ["DATABASE_URL"]
else:
    # Default to Docker service name "db" when running locally
    TEST_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@db:5432/{DB_NAME}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DB_NAME"] = DB_NAME
os.environ["DB_USER"] = DB_USER
os.environ["DB_PASS"] = DB_PASS
# Set required environment variables to avoid config errors
os.environ["AWS_ACCESS_KEY_ID"] = "test_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test_secret"
os.environ["COINGECKO_API_KEY"] = "test_api_key"
os.environ["S3_BUCKET_NAME"] = "test_bucket"

from src.database import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test using PostgreSQL with pgvector.

    This fixture:
    1. Creates a PostgreSQL engine (with pgvector support)
    2. Creates all tables (including vector columns)
    3. Provides a test session
    4. Cleans up after each test
    """
    # Create PostgreSQL engine
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    # Enable pgvector extension (if not already enabled)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Drop all tables before creating (ensures clean state)
    Base.metadata.drop_all(bind=engine)

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

    # Create a test session for the fixture
    test_session = TestingSessionLocal()

    yield test_session

    # Clean up
    test_session.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_db):
    """Create a test client with database dependency overridden."""
    return TestClient(app)


# Sample news article fixture removed - database tests removed for now


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
