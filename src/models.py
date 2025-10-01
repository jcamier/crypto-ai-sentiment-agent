"""
SQLAlchemy models for the crypto sentiment agent.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ARRAY
from sqlalchemy.sql import func
from src.database import Base


class NewsArticle(Base):
    """Model for storing crypto news articles."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    source = Column(String(255))
    url = Column(Text)
    published_at = Column(DateTime)
    tokens_mentioned = Column(ARRAY(String))  # Array of crypto tokens mentioned
    sentiment = Column(String(20))  # bullish, bearish, neutral
    confidence_score = Column(Float)
    s3_bucket_source = Column(String(255))  # S3 bucket where article was sourced from
    s3_key_source = Column(String(500))  # S3 key/path of the source file
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', sentiment='{self.sentiment}')>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "tokens_mentioned": self.tokens_mentioned or [],
            "sentiment": self.sentiment,
            "confidence_score": self.confidence_score,
            "s3_bucket_source": self.s3_bucket_source,
            "s3_key_source": self.s3_key_source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
