"""
Embedding Service using Amazon Bedrock Titan Text Embeddings V2
Generates vector embeddings for semantic search.
"""

import json
import logging

import boto3
from decouple import config

from src.metrics import bedrock_api_calls_total, embedding_generation_duration_seconds

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Amazon Bedrock Titan V2."""

    def __init__(self):
        """Initialize Bedrock client for embeddings."""
        self.aws_access_key = config("AWS_ACCESS_KEY_ID", default="")
        self.aws_secret_key = config("AWS_SECRET_ACCESS_KEY", default="")
        self.aws_region = config("AWS_BEDROCK_REGION", default="us-east-1")

        # Create Bedrock client
        if self.aws_access_key and self.aws_secret_key:
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region,
            )
        else:
            # Use IAM role (for EC2)
            self.bedrock_client = boto3.client(
                "bedrock-runtime", region_name=self.aws_region
            )

        self.model_id = config(
            "BEDROCK_EMBEDDING_MODEL_ID", default="amazon.titan-embed-text-v2:0"
        )
        logger.info(f"EmbeddingService initialized with model: {self.model_id}")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for given text using Bedrock Titan V2.

        Args:
            text: Text to embed (max 8K tokens for Titan V2)

        Returns:
            List of floats representing the embedding vector (1024 dimensions for V2)

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Truncate text if too long (rough estimate: 1 token ≈ 4 chars)
            max_chars = 25000  # Conservative limit for 8K tokens
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Truncated text to {max_chars} characters")

            # Prepare request body for Titan V2
            body = json.dumps({"inputText": text})

            # Track embedding generation time
            with embedding_generation_duration_seconds.time():
                # Call Bedrock API
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=body,
                    contentType="application/json",
                    accept="application/json",
                )

            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding")

            if not embedding:
                raise ValueError("No embedding returned from Bedrock")

            # Track successful API call
            bedrock_api_calls_total.labels(
                model=self.model_id, operation="embedding", status="success"
            ).inc()

            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Track failed API call
            bedrock_api_calls_total.labels(
                model=self.model_id, operation="embedding", status="error"
            ).inc()
            # Return zero vector as fallback
            return [0.0] * 1024

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Titan doesn't support batch API, so we call individually.
        Consider implementing rate limiting and retry logic for production.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                logger.info(f"Generated embedding {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i+1}: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 1024)

        return embeddings
