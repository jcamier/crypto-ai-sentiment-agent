# Crypto News & Sentiment Agent - Day 1 Specification

## Project Overview
Build a crypto news fetcher agent that processes news articles and performs basic sentiment analysis using local LLM models.

## Why This Approach?
We're using **two data sources** (S3 PDFs + CoinGecko API) to give you the best learning experience:

### Enterprise Experience
- **S3 Integration**: Learn to work with AWS S3 buckets (extremely common in companies)
- **boto3 Skills**: Master the standard Python library for AWS services
- **Cloud Data Patterns**: Understand how enterprises store and access data

### Real-time Skills
- **Live API Integration**: Experience fetching real-time data from external APIs
- **Rate Limiting**: Learn to handle API constraints and implement proper throttling
- **Dynamic Data**: Work with data that changes constantly (real-world scenario)

### Testability & Quality Assurance
- **S3 PDFs**: Provide consistent, reproducible test data for reliable testing
- **Predictable Results**: All students get the same 15 articles for validation
- **Quality Control**: Test your sentiment analysis against known good data

### Best of Both Worlds
- **Stable Testing**: S3 data ensures your code works consistently
- **Dynamic Real-world**: Live API data keeps the project relevant and current
- **Production Ready**: Learn patterns used in actual production systems

### Progressive Learning
- **Start Simple**: Begin with structured PDF data (easier to parse)
- **Add Complexity**: Progress to live API integration with error handling
- **Build Confidence**: Master one approach before adding the next layer

## Day 1 Requirements

### Core Functionality
- **S3 News Fetcher**: Download and process 15 crypto news PDFs from S3 bucket (reproducible testing)
- **Live API Service**: FastAPI service to fetch latest crypto news from CoinGecko API (real-time data)
- **Data Parser**: Structure and clean news data (title, content, source, timestamp)
- **Sentiment Classifier**: Basic sentiment analysis using local LLM (bullish/bearish/neutral)
- **Data Storage**: Store raw news data in local Postgres database

### Technical Stack
- **Language**: Python
- **LLM**: Local Ollama (llama3.2:latest)
- **Database**: PostgreSQL (Docker container)
- **Containerization**: Docker & Docker Compose
- **Web Framework**: FastAPI for API service
- **AWS Integration**: boto3 for S3 access
- **APIs**: CoinGecko API (live data) + S3 bucket (reproducible testing)

### Data Sources
- **S3 Bucket**: 15 crypto news PDFs (reproducible testing data)
  - Bucket: `crypto-news-pdfs-sep-2025`
  - Focus: BTC, ETH, SOL, USDT, FDUSD articles
  - Sources: CoinDesk, Cointelegraph, Decrypt, The Block, CCN
- **Live API**: CoinGecko API for real-time crypto news
  - Endpoint: `https://api.coingecko.com/api/v3/search/trending`
  - Rate limiting: 10-30 calls/minute (free tier)

### Database Schema
```sql
-- News articles table
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(255),
    url TEXT,
    published_at TIMESTAMP,
    tokens_mentioned TEXT[], -- Array of crypto tokens mentioned
    sentiment VARCHAR(20), -- bullish, bearish, neutral
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Integration
- **S3 Integration**: Use boto3 to download PDFs from S3 bucket
- **FastAPI Service**: Create REST endpoints for CoinGecko news fetching
- **PDF Processing**: Extract text content from downloaded PDFs
- **Rate Limiting**: Handle CoinGecko API rate limits gracefully
- **Error Handling**: Graceful fallback between S3 and live API sources

### Sentiment Analysis
- Use local Ollama model for sentiment classification
- Classify each article as: bullish, bearish, or neutral
- Include confidence score (0.0 to 1.0)
- Extract mentioned crypto tokens from article content

### Docker Setup
- **Container 1**: Python application (S3 fetcher + FastAPI + sentiment analysis)
- **Container 2**: PostgreSQL database
- **Docker Compose**: Orchestrate both containers
- **Environment variables**: AWS credentials, CoinGecko API key, database connection strings

### Success Criteria
- [ ] Successfully download and process all 15 PDFs from S3 bucket
- [ ] Create FastAPI service with CoinGecko integration
- [ ] Parse and structure news data correctly (PDFs + API responses)
- [ ] Perform sentiment analysis using local LLM
- [ ] Store data in PostgreSQL database
- [ ] Run entire stack with `docker compose up`
- [ ] Handle basic error cases (S3 failures, API rate limits, database connection issues)

### Deliverables
- Working Docker Compose setup
- Python application with S3 PDF processing and FastAPI service
- PostgreSQL database with proper schema
- Basic logging and error handling
- README with setup instructions
- Test suite for S3 PDF processing (reproducible results)

