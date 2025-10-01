"""
Tests for database models.
"""

import pytest
from datetime import datetime
from src.models import NewsArticle


def test_news_article_creation():
    """Test creating a NewsArticle instance."""
    article = NewsArticle(
        title="Test Article",
        content="Test content",
        source="TestSource",
        sentiment="bullish",
        confidence_score=0.85
    )

    assert article.title == "Test Article"
    assert article.content == "Test content"
    assert article.source == "TestSource"
    assert article.sentiment == "bullish"
    assert article.confidence_score == 0.85


def test_news_article_to_dict():
    """Test converting NewsArticle to dictionary."""
    now = datetime.now()
    article = NewsArticle(
        id=1,
        title="Test Article",
        content="Test content",
        source="TestSource",
        published_at=now,
        tokens_mentioned=["BTC"],
        sentiment="bullish",
        confidence_score=0.85,
        created_at=now
    )

    article_dict = article.to_dict()

    assert article_dict["id"] == 1
    assert article_dict["title"] == "Test Article"
    assert article_dict["content"] == "Test content"
    assert article_dict["source"] == "TestSource"
    assert article_dict["tokens_mentioned"] == ["BTC"]
    assert article_dict["sentiment"] == "bullish"
    assert article_dict["confidence_score"] == 0.85
