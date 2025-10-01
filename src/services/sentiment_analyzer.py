"""
Amazon Bedrock sentiment analysis service for crypto news.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Tuple
from decouple import config
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import NewsArticle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Service for analyzing sentiment of crypto news using Amazon Bedrock."""

    def __init__(self):
        """Initialize Bedrock client and configuration."""
        self.aws_access_key = config("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = config("AWS_SECRET_ACCESS_KEY")
        self.aws_region = config("AWS_BEDROCK_REGION", default="us-east-1")
        self.model_id = config("BEDROCK_MODEL_ID", default="anthropic.claude-3-haiku-20240307-v1:0")

        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )

    def _create_sentiment_prompt(self, title: str, content: str) -> str:
        """Create a prompt for sentiment analysis."""
        return f"""
You are a financial sentiment analysis expert specializing in cryptocurrency news.
Analyze the following crypto news article and determine its sentiment.

Title: {title}

Content: {content[:1000]}...

Please analyze the sentiment and provide your response in the following JSON format:
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your analysis",
    "tokens_mentioned": ["BTC", "ETH", "SOL", ...]
}}

Guidelines:
- "bullish": Positive sentiment, optimistic outlook, price increases expected
- "bearish": Negative sentiment, pessimistic outlook, price decreases expected
- "neutral": Balanced or factual reporting without clear directional bias
- confidence_score: 0.0 (low confidence) to 1.0 (high confidence)
- Extract all cryptocurrency tokens mentioned in the article
- Focus on the overall market sentiment, not just individual token mentions

Respond only with valid JSON, no additional text.
"""

    def _parse_bedrock_response(self, response_body: str) -> Dict[str, Any]:
        """Parse Bedrock response and extract sentiment data."""
        try:
            # Extract JSON from response
            response_text = response_body.strip()

            # Try to find JSON in the response
            if response_text.startswith('{') and response_text.endswith('}'):
                return json.loads(response_text)
            else:
                # Look for JSON within the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise ValueError("No valid JSON found in response")

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response was: {response_body}")
            return {
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "reasoning": "Failed to parse response",
                "tokens_mentioned": []
            }
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "reasoning": "Error in analysis",
                "tokens_mentioned": []
            }

    def analyze_sentiment(self, title: str, content: str) -> Dict[str, Any]:
        """Analyze sentiment of a news article using Bedrock."""
        try:
            # Create prompt
            prompt = self._create_sentiment_prompt(title, content)

            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            content_text = response_body['content'][0]['text']

            # Parse the sentiment analysis result
            sentiment_data = self._parse_bedrock_response(content_text)

            logger.info(f"Sentiment analysis completed: {sentiment_data['sentiment']} (confidence: {sentiment_data['confidence_score']})")
            return sentiment_data

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                "sentiment": "neutral",
                "confidence_score": 0.5,
                "reasoning": f"Analysis failed: {str(e)}",
                "tokens_mentioned": []
            }

    def analyze_article(self, article: NewsArticle) -> NewsArticle:
        """Analyze sentiment of a single article and update it."""
        try:
            # Perform sentiment analysis
            sentiment_data = self.analyze_sentiment(article.title, article.content or "")

            # Update article with sentiment data
            article.sentiment = sentiment_data["sentiment"]
            article.confidence_score = sentiment_data["confidence_score"]

            # Update tokens mentioned if we found additional ones
            if sentiment_data.get("tokens_mentioned"):
                existing_tokens = set(article.tokens_mentioned or [])
                new_tokens = set(sentiment_data["tokens_mentioned"])
                article.tokens_mentioned = list(existing_tokens.union(new_tokens))

            logger.info(f"Updated article '{article.title[:50]}...' with sentiment: {article.sentiment}")
            return article

        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            # Set default values on error
            article.sentiment = "neutral"
            article.confidence_score = 0.5
            return article

    def analyze_articles_batch(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Analyze sentiment for a batch of articles."""
        analyzed_articles = []

        for article in articles:
            try:
                analyzed_article = self.analyze_article(article)
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                logger.error(f"Error analyzing article {article.id}: {e}")
                # Add article with default sentiment
                article.sentiment = "neutral"
                article.confidence_score = 0.5
                analyzed_articles.append(article)

        return analyzed_articles

    def update_articles_in_db(self, articles: List[NewsArticle]) -> int:
        """Update articles in database with sentiment analysis results."""
        db = SessionLocal()
        updated_count = 0

        try:
            for article in articles:
                # Update the article in database
                db.merge(article)
                updated_count += 1

            db.commit()
            logger.info(f"Updated {updated_count} articles with sentiment analysis")

        except Exception as e:
            logger.error(f"Error updating articles in database: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return updated_count


def analyze_all_articles():
    """Main function to analyze sentiment for all articles without sentiment."""
    try:
        db = SessionLocal()
        analyzer = SentimentAnalyzer()

        # Get articles without sentiment analysis
        articles = db.query(NewsArticle).filter(
            NewsArticle.sentiment.is_(None)
        ).all()

        if not articles:
            logger.info("No articles found that need sentiment analysis")
            return

        logger.info(f"Found {len(articles)} articles to analyze")

        # Analyze articles
        analyzed_articles = analyzer.analyze_articles_batch(articles)

        # Update in database
        updated_count = analyzer.update_articles_in_db(analyzed_articles)

        logger.info(f"Successfully analyzed sentiment for {updated_count} articles")

    except Exception as e:
        logger.error(f"Error in analyze_all_articles: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    analyze_all_articles()
