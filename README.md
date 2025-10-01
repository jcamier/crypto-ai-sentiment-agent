# Crypto News & Sentiment Agent

### An Agentic AI Workflow for Crypto News Sentiment Analysis

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock access
- CoinGecko API key (free tier)
- Docker and Docker Compose
- Python 3.11+

### 1. Setup Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials:
# - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# - S3_BUCKET_NAME (your own bucket)
# - COINGECKO_API_KEY
```

### 2. Test Setup
```bash
# Run setup test to verify configuration
python test_setup.py
```

### 3. Start Services
```bash
# Start Docker containers
make up

# Initialize database
make setup

# Process S3 PDFs (15 crypto news articles)
make process-s3

# Fetch live news from CoinGecko
make fetch-coingecko

# Analyze sentiment using Amazon Bedrock
make analyze-sentiment

# Test API endpoints
make test-api
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and available endpoints |
| `/health` | GET | Health check for Docker |
| `/api/news/` | GET | Get news articles with filtering |
| `/api/sentiment/` | GET | Get sentiment analysis results |
| `/api/stats/` | GET | Database statistics |
| `/api/process/s3/` | POST | Process S3 PDFs |
| `/api/fetch/live/` | POST | Fetch live news from CoinGecko |
| `/api/analyze/sentiment/` | POST | Analyze sentiment for articles |

### Example API Usage
```bash
# Get all news articles
curl http://localhost:8000/api/news/

# Get bullish sentiment articles only
curl "http://localhost:8000/api/news/?sentiment=bullish"

# Get articles mentioning BTC
curl "http://localhost:8000/api/news/?token=BTC"

# Get sentiment analysis for BTC
curl "http://localhost:8000/api/sentiment/?token=BTC"
```

## 🏗️ Architecture

- **FastAPI**: Web framework and REST API
- **PostgreSQL + pgvector**: Database with vector support for future embeddings
- **Amazon Bedrock**: LLM service for sentiment analysis (Claude 3 Haiku)
- **Docker**: Containerized deployment
- **boto3**: AWS SDK for S3 and Bedrock integration
- **CoinGecko API**: Live crypto news data

## 📁 Project Structure

```
src/
├── main.py                 # FastAPI application
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
└── services/
    ├── s3_processor.py    # S3 PDF processing
    ├── coingecko_service.py # CoinGecko API integration
    └── sentiment_analyzer.py # Bedrock sentiment analysis
```

## 🔧 Development Commands

```bash
# Development
make install    # Install Python dependencies
make lint       # Run code linting
make format     # Format code with black/isort
make test       # Run tests

# Docker operations
make up         # Start services
make down       # Stop services
make build      # Build images
make logs       # View logs
make shell      # Shell into container

# Data processing
make process-s3      # Process S3 PDFs
make fetch-coingecko # Fetch live news
make analyze-sentiment # Run sentiment analysis
```

## 📋 Five-Day Bootcamp Overview

📋 **[View Detailed Bootcamp Outline](agentic_ai_bootcamp_outline.md)** - Complete curriculum
📋 **[View Day 1 Specification](spec-day-1.md)** - Detailed Day 1 requirements

- **Day 1**: ✅ Build crypto news fetcher agent with Docker containers
- **Day 2**: Set up AWS infrastructure with CI/CD pipeline using GitHub Actions and Terraform
- **Day 3**: Implement embeddings, sentiment analysis, and observability with Prometheus/Grafana
- **Day 4**: Migrate to Amazon Bedrock with guardrails, retry logic, and evaluation harness
- **Day 5**: Deploy production dashboard with CloudFront and complete crypto sentiment trends

## 🎯 Day 1 Success Criteria

- [x] Successfully download and process all 15 PDFs from S3 bucket
- [x] Create FastAPI service with CoinGecko integration
- [x] Parse and structure news data correctly (PDFs + API responses)
- [x] Perform sentiment analysis using Amazon Bedrock
- [x] Store data in PostgreSQL database
- [x] Run entire stack with `docker compose up`
- [x] Handle basic error cases (S3 failures, API rate limits, database connection issues)

## 📰 News Sources

The project processes 15 crypto news articles from September 2025, covering:
- **Bitcoin (BTC)**: Price analysis, market trends, ETF developments
- **Ethereum (ETH)**: Price movements, ETF inflows, market corrections
- **Tether (USDT)**: Reserve management, liquidity signals
- **Solana (SOL)**: ETF prospects, ecosystem developments
- **First Digital USD (FDUSD)**: Price predictions, market outlook

Sources include CoinDesk, Decrypt, Cointelegraph, The Block, CCN, and CoinMarketCap.

## 🔒 Security Notes

- Never commit `.env` files to version control
- Use IAM roles with least-privilege access
- Configure CORS appropriately for production
- Consider using AWS Secrets Manager for production deployments

