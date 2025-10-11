"""add_pgvector_embeddings

Revision ID: c81f198f1e2c
Revises:
Create Date: 2025-10-11 13:16:53.797331

This migration adds pgvector extension support and embedding columns
to the news_articles table for semantic search functionality.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c81f198f1e2c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add pgvector extension and embedding columns to news_articles table.

    Changes:
    - Enable pgvector extension (if not already enabled)
    - Add embedding column (vector(1024) for Titan v2)
    - Add embedding_model column to track which model generated the embedding
    - Add embedding_generated_at timestamp
    - Create IVFFlat index for fast similarity search
    """
    # Enable pgvector extension (idempotent - safe to run multiple times)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column (1024 dimensions for Titan Text Embeddings V2)
    # Using raw SQL because pgvector type needs special handling
    op.execute('''
        ALTER TABLE news_articles
        ADD COLUMN IF NOT EXISTS embedding vector(1024)
    ''')

    # Add metadata columns for tracking embeddings
    op.add_column(
        'news_articles',
        sa.Column('embedding_model', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'news_articles',
        sa.Column('embedding_generated_at', sa.DateTime(), nullable=True)
    )

    # Create IVFFlat index for fast cosine similarity search
    # lists=100 is good for ~10K-100K rows (adjust based on data size)
    # For more data, consider HNSW index instead
    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_news_articles_embedding
        ON news_articles
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')

    # Add comment to document the index
    op.execute('''
        COMMENT ON INDEX idx_news_articles_embedding IS
        'IVFFlat index for fast cosine similarity search on embeddings.
        Adjust lists parameter based on dataset size:
        - 10K rows: lists=100,
        - 100K rows: lists=1000,
        - 1M+ rows: consider HNSW index'
    ''')


def downgrade() -> None:
    """
    Remove embedding columns and index (rollback migration).

    Note: This does NOT drop the pgvector extension as it may be used elsewhere.
    """
    # Drop the index
    op.execute('DROP INDEX IF EXISTS idx_news_articles_embedding')

    # Drop the metadata columns
    op.drop_column('news_articles', 'embedding_generated_at')
    op.drop_column('news_articles', 'embedding_model')

    # Drop the embedding column
    op.execute('ALTER TABLE news_articles DROP COLUMN IF EXISTS embedding')

    # Note: We intentionally do NOT drop the vector extension
    # as it may be used by other tables or databases
    # If you need to drop it manually, run: DROP EXTENSION vector;
