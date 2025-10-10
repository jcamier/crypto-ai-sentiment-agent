"""
Crypto News & Sentiment Agent - FastAPI Application
Main entry point for the crypto sentiment analysis service.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from decouple import config
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db, init_db, setup_pgvector
from models import NewsArticle
from services.coingecko_service import fetch_latest_news
from services.s3_processor import process_s3_pdfs
from services.sentiment_analyzer import analyze_all_articles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


def verify_api_key(api_key: str = Query(..., description="API key for authentication")):
    """Verify API key for protected endpoints."""
    expected_key = config("API_KEY", default="crypto-agent-secret-key")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    try:
        init_db()
        setup_pgvector()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Crypto News & Sentiment Agent",
    description="Agentic AI workflow for crypto news sentiment analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Crypto News & Sentiment Agent",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "news": "/api/news/",
            "sentiment": "/api/sentiment/",
            "process_s3": "/api/process/s3/",
            "fetch_live": "/api/fetch/live/",
            "analyze": "/api/analyze/sentiment/",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks."""
    return {"status": "healthy", "service": "crypto-sentiment-agent"}


@app.get("/api/news/")
@limiter.limit("30/minute")
async def get_news(
    request: Request,
    api_key: str = Depends(verify_api_key),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sentiment: str | None = Query(None, pattern="^(bullish|bearish|neutral)$"),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get processed news articles from database."""
    try:
        query = db.query(NewsArticle)

        # Apply filters
        if sentiment:
            query = query.filter(NewsArticle.sentiment == sentiment)

        if token:
            query = query.filter(NewsArticle.tokens_mentioned.contains([token.upper()]))

        # Get total count
        total_count = query.count()

        # Apply pagination
        articles = (
            query.order_by(NewsArticle.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "articles": [article.to_dict() for article in articles],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching news articles"
        ) from None


@app.get("/api/sentiment/")
@limiter.limit("30/minute")
async def get_sentiment(
    request: Request,
    api_key: str = Depends(verify_api_key),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis results aggregated by token."""
    try:
        query = db.query(NewsArticle).filter(NewsArticle.sentiment.isnot(None))

        if token:
            query = query.filter(NewsArticle.tokens_mentioned.contains([token.upper()]))

        articles = query.all()

        # Aggregate sentiment data
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        total_confidence = 0
        token_mentions = {}

        for article in articles:
            if article.sentiment in sentiment_counts:
                sentiment_counts[article.sentiment] += 1

            if article.confidence_score:
                total_confidence += article.confidence_score

            # Count token mentions
            for token_mentioned in article.tokens_mentioned or []:
                token_mentions[token_mentioned] = (
                    token_mentions.get(token_mentioned, 0) + 1
                )

        total_articles = len(articles)
        avg_confidence = total_confidence / total_articles if total_articles > 0 else 0

        # Determine overall sentiment
        overall_sentiment = (
            max(sentiment_counts, key=sentiment_counts.get)
            if total_articles > 0
            else "neutral"
        )

        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_distribution": sentiment_counts,
            "total_articles": total_articles,
            "average_confidence": round(avg_confidence, 3),
            "token_mentions": token_mentions,
            "filtered_by_token": token,
        }

    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching sentiment analysis"
        ) from None


@app.post("/api/process/s3/")
@limiter.limit("5/minute")
async def process_s3_endpoint(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Process S3 PDFs and store in database."""
    try:
        process_s3_pdfs()
        return {"message": "S3 PDFs processed successfully", "status": "completed"}
    except Exception as e:
        logger.error(f"Error processing S3 PDFs: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing S3 PDFs: {str(e)}"
        ) from None


@app.post("/api/fetch/live/")
@limiter.limit("5/minute")
async def fetch_live_news(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Fetch latest crypto news from CoinGecko API."""
    try:
        await fetch_latest_news()
        return {"message": "Live news fetched successfully", "status": "completed"}
    except Exception as e:
        logger.error(f"Error fetching live news: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching live news: {str(e)}"
        ) from None


@app.post("/api/analyze/sentiment/")
@limiter.limit("5/minute")
async def analyze_sentiment_endpoint(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Analyze sentiment for all articles without sentiment data."""
    try:
        analyze_all_articles()
        return {
            "message": "Sentiment analysis completed successfully",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing sentiment: {str(e)}"
        ) from None


@app.get("/api/stats/")
@limiter.limit("30/minute")
async def get_stats(
    request: Request,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Get database statistics."""
    try:
        total_articles = db.query(NewsArticle).count()
        articles_with_sentiment = (
            db.query(NewsArticle).filter(NewsArticle.sentiment.isnot(None)).count()
        )
        articles_without_sentiment = total_articles - articles_with_sentiment

        # Count by source
        sources = (
            db.query(NewsArticle.source, db.func.count(NewsArticle.id))
            .group_by(NewsArticle.source)
            .all()
        )

        return {
            "total_articles": total_articles,
            "articles_with_sentiment": articles_with_sentiment,
            "articles_without_sentiment": articles_without_sentiment,
            "sources": dict(sources),
        }

    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=500, detail="Error fetching statistics"
        ) from None


if __name__ == "__main__":
    # Get configuration from environment
    host = config("HOST", default="0.0.0.0")
    port = config("PORT", default=8000)
    debug = config("DEBUG", default=True, cast=bool)

    # Run the application
    uvicorn.run("main:app", host=host, port=port, reload=debug)
