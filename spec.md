# Crypto News & Sentiment Agent - Day 1 Specification

## Project Overview
Build a crypto news fetcher agent that processes news articles and performs basic sentiment analysis using local LLM models.

## Day 1 Requirements

### Core Functionality
- **News Fetcher**: Retrieve latest crypto news from public APIs (focus on BTC, ETH, SOL)
- **Data Parser**: Structure and clean news data (title, content, source, timestamp)
- **Sentiment Classifier**: Basic sentiment analysis using local LLM (bullish/bearish/neutral)
- **Data Storage**: Store raw news data in local Postgres database

### Technical Stack
- **Language**: Python
- **LLM**: Local Ollama (llama3.2:latest)
- **Database**: PostgreSQL (Docker container)
- **Containerization**: Docker & Docker Compose
- **APIs**: CoinGecko API, CryptoPanic API, or NewsAPI

### Data Sources
- Primary focus: Bitcoin (BTC), Ethereum (ETH), Solana (SOL)
- News sources: CoinDesk, Cointelegraph, Decrypt, The Block
- API endpoints for real-time crypto news

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
- Fetch news from at least 2 crypto news APIs
- Handle rate limiting and API errors gracefully
- Parse JSON responses and extract relevant fields
- Store API responses in structured format

### Sentiment Analysis
- Use local Ollama model for sentiment classification
- Classify each article as: bullish, bearish, or neutral
- Include confidence score (0.0 to 1.0)
- Extract mentioned crypto tokens from article content

### Docker Setup
- **Container 1**: Python application (news fetcher + sentiment analysis)
- **Container 2**: PostgreSQL database
- **Docker Compose**: Orchestrate both containers
- **Environment variables**: API keys, database connection strings

### Success Criteria
- [ ] Successfully fetch crypto news from APIs
- [ ] Parse and structure news data correctly
- [ ] Perform sentiment analysis using local LLM
- [ ] Store data in PostgreSQL database
- [ ] Run entire stack with `docker compose up`
- [ ] Handle basic error cases (API failures, database connection issues)

### Deliverables
- Working Docker Compose setup
- Python application with news fetching and sentiment analysis
- PostgreSQL database with proper schema
- Basic logging and error handling
- README with setup instructions

