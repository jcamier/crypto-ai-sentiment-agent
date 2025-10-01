"""
Crypto News & Sentiment Agent - FastAPI Application
Main entry point for the crypto sentiment analysis service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from decouple import config

# Create FastAPI app
app = FastAPI(
    title="Crypto News & Sentiment Agent",
    description="Agentic AI workflow for crypto news sentiment analysis",
    version="0.1.0"
)

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
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks."""
    return {
        "status": "healthy",
        "service": "crypto-sentiment-agent"
    }

@app.get("/api/news/")
async def get_news():
    """Get processed news articles from database."""
    # TODO: Implement news retrieval
    return {
        "message": "News endpoint - to be implemented",
        "articles": []
    }

@app.get("/api/sentiment/")
async def get_sentiment():
    """Get sentiment analysis results."""
    # TODO: Implement sentiment analysis
    return {
        "message": "Sentiment endpoint - to be implemented",
        "results": []
    }

if __name__ == "__main__":
    # Get configuration from environment
    host = config("HOST", default="0.0.0.0")
    port = config("PORT", default=8000)
    debug = config("DEBUG", default=True, cast=bool)

    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
