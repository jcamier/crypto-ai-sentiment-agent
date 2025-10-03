"""
Database configuration and setup for the crypto sentiment agent.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:postgres@db:5432/crypto_news")
DB_NAME = config("DB_NAME", default="crypto_news")
DB_USER = config("DB_USER", default="postgres")
DB_PASS = config("DB_PASS", default="postgres")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with required tables."""
    try:
        # Import models to ensure they are registered with Base
        from models import NewsArticle

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def setup_pgvector():
    """Setup pgvector extension for vector operations."""
    try:
        with engine.connect() as conn:
            # Enable pgvector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

        logger.info("pgvector extension enabled successfully")

    except Exception as e:
        logger.error(f"pgvector setup failed: {e}")
        raise

def test_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
