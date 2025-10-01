"""
CoinGecko API service for fetching live crypto news.
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decouple import config
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import NewsArticle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoinGeckoService:
    """Service for fetching crypto news from CoinGecko API."""

    def __init__(self):
        """Initialize CoinGecko API client."""
        self.api_key = config("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "x-cg-demo-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to CoinGecko API with rate limiting."""
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params or {},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def _extract_tokens_from_text(self, text: str) -> List[str]:
        """Extract crypto token symbols from text."""
        # Common crypto tokens to look for
        crypto_tokens = [
            "BTC", "BITCOIN", "ETH", "ETHEREUM", "SOL", "SOLANA",
            "USDT", "USDC", "BNB", "ADA", "XRP", "DOGE", "DOT",
            "AVAX", "MATIC", "LINK", "UNI", "LTC", "BCH", "ATOM"
        ]

        text_upper = text.upper()
        found_tokens = []

        for token in crypto_tokens:
            if token in text_upper:
                found_tokens.append(token)

        return list(set(found_tokens))  # Remove duplicates

    def _parse_coingecko_article(self, article_data: Dict[str, Any]) -> NewsArticle:
        """Parse CoinGecko article data into NewsArticle model."""
        try:
            # Extract tokens from title and content
            title = article_data.get("title", "")
            content = article_data.get("content", "")
            full_text = f"{title} {content}"

            tokens_mentioned = self._extract_tokens_from_text(full_text)

            # Parse published date
            published_at = None
            if "published_at" in article_data:
                try:
                    published_at = datetime.fromisoformat(
                        article_data["published_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    published_at = datetime.now()

            article = NewsArticle(
                title=title,
                content=content,
                source=article_data.get("source", "CoinGecko"),
                url=article_data.get("url"),
                published_at=published_at,
                tokens_mentioned=tokens_mentioned,
                sentiment=None,  # Will be filled by sentiment analysis
                confidence_score=None,
                s3_bucket_source=None,  # Not from S3
                s3_key_source=None
            )

            return article

        except Exception as e:
            logger.error(f"Error parsing CoinGecko article: {e}")
            raise

    async def fetch_trending_news(self) -> List[NewsArticle]:
        """Fetch trending crypto news from CoinGecko."""
        try:
            # Fetch trending coins first
            trending_data = await self._make_request("/search/trending")

            articles = []

            # Process trending coins data
            if "coins" in trending_data:
                for coin_data in trending_data["coins"]:
                    coin_info = coin_data.get("item", {})

                    # Create a news-like entry from trending data
                    article = NewsArticle(
                        title=f"Trending: {coin_info.get('name', 'Unknown')} ({coin_info.get('symbol', '').upper()})",
                        content=f"Coin {coin_info.get('name', 'Unknown')} is trending with rank #{coin_info.get('market_cap_rank', 'N/A')}",
                        source="CoinGecko Trending",
                        url=f"https://www.coingecko.com/en/coins/{coin_info.get('id', '')}",
                        published_at=datetime.now(),
                        tokens_mentioned=[coin_info.get('symbol', '').upper()] if coin_info.get('symbol') else [],
                        sentiment=None,
                        confidence_score=None,
                        s3_bucket_source=None,
                        s3_key_source=None
                    )
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} trending items from CoinGecko")
            return articles

        except Exception as e:
            logger.error(f"Error fetching trending news: {e}")
            return []

    async def fetch_coin_news(self, coin_id: str = "bitcoin") -> List[NewsArticle]:
        """Fetch news for a specific coin (Note: This endpoint may not be available in free tier)."""
        try:
            # This endpoint might require a paid plan
            news_data = await self._make_request(f"/coins/{coin_id}/news")

            articles = []
            for article_data in news_data:
                article = self._parse_coingecko_article(article_data)
                articles.append(article)

            logger.info(f"Fetched {len(articles)} news articles for {coin_id}")
            return articles

        except Exception as e:
            logger.warning(f"Could not fetch coin news (may require paid plan): {e}")
            return []

    def save_articles_to_db(self, articles: List[NewsArticle]) -> int:
        """Save fetched articles to database."""
        db = SessionLocal()
        saved_count = 0

        try:
            for article in articles:
                # Check if article already exists (by title and source)
                existing = db.query(NewsArticle).filter(
                    NewsArticle.title == article.title,
                    NewsArticle.source == article.source
                ).first()

                if not existing:
                    db.add(article)
                    saved_count += 1
                else:
                    logger.info(f"Article already exists: {article.title}")

            db.commit()
            logger.info(f"Saved {saved_count} new articles to database")

        except Exception as e:
            logger.error(f"Error saving articles to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return saved_count


async def fetch_latest_news():
    """Main function to fetch latest news from CoinGecko."""
    try:
        service = CoinGeckoService()

        # Fetch trending news
        articles = await service.fetch_trending_news()

        if articles:
            # Save to database
            saved_count = service.save_articles_to_db(articles)
            logger.info(f"Successfully fetched and saved {saved_count} articles from CoinGecko")
        else:
            logger.warning("No articles were fetched from CoinGecko")

    except Exception as e:
        logger.error(f"Error in fetch_latest_news: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(fetch_latest_news())
