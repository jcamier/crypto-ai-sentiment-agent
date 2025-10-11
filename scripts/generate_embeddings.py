#!/usr/bin/env python3
"""
Generate embeddings for all articles in the database.

This script:
1. Fetches all articles without embeddings
2. Generates embeddings using Bedrock Titan V2
3. Updates the database with embeddings and metadata
"""

import sys
import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

# Add src to path for imports
sys.path.insert(0, "/app")

from src.database import get_db, engine
from src.models import NewsArticle
from src.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_embeddings_for_articles(batch_size: int = 10):
    """
    Generate embeddings for all articles that don't have them.

    Args:
        batch_size: Number of articles to process in each batch
    """
    embedding_service = EmbeddingService()

    # Get database session
    db: Session = next(get_db())

    try:
        # Count articles without embeddings
        total_without_embeddings = (
            db.query(func.count(NewsArticle.id))
            .filter(NewsArticle.embedding.is_(None))
            .scalar()
        )

        # Count total articles
        total_articles = db.query(func.count(NewsArticle.id)).scalar()

        logger.info(f"📊 Total articles: {total_articles}")
        logger.info(f"📊 Articles without embeddings: {total_without_embeddings}")
        logger.info(f"📊 Articles with embeddings: {total_articles - total_without_embeddings}")

        if total_without_embeddings == 0:
            logger.info("✅ All articles already have embeddings!")
            return

        logger.info(f"🚀 Starting embedding generation for {total_without_embeddings} articles...")
        logger.info(f"📦 Processing in batches of {batch_size}")

        # Fetch articles without embeddings
        articles = (
            db.query(NewsArticle)
            .filter(NewsArticle.embedding.is_(None))
            .all()
        )

        successful = 0
        failed = 0

        for idx, article in enumerate(articles, 1):
            try:
                # Combine title and description for embedding
                text_to_embed = f"{article.title}\n\n{article.description or ''}"

                # Generate embedding
                embedding = embedding_service.generate_embedding(text_to_embed)

                # Check if embedding was generated (not fallback zeros)
                if sum(embedding) == 0:
                    logger.warning(f"⚠️  [{idx}/{total_without_embeddings}] Fallback embedding for article {article.id}: {article.title[:50]}...")
                    failed += 1
                    continue

                # Update article with embedding
                article.embedding = embedding
                article.embedding_model = embedding_service.model_id
                article.embedding_generated_at = datetime.utcnow()

                db.commit()

                successful += 1
                logger.info(f"✓ [{idx}/{total_without_embeddings}] Generated embedding for: {article.title[:60]}...")

                # Commit batch
                if idx % batch_size == 0:
                    logger.info(f"💾 Committed batch at {idx}/{total_without_embeddings}")

            except Exception as e:
                logger.error(f"❌ [{idx}/{total_without_embeddings}] Failed for article {article.id}: {e}")
                db.rollback()
                failed += 1

        # Final summary
        logger.info("=" * 70)
        logger.info(f"✅ Embedding generation complete!")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Total processed: {successful + failed}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Fatal error during embedding generation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_embeddings_for_articles()

