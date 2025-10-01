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
- **Sentiment Classifier**: Basic sentiment analysis using Amazon Bedrock (bullish/bearish/neutral)
- **Data Storage**: Store raw news data in local Postgres database

### Technical Stack
- **Language**: Python
- **LLM**: Amazon Bedrock (Claude 3 Haiku - cost-effective)
- **Database**: PostgreSQL (Docker container)
- **Containerization**: Docker & Docker Compose
- **Web Framework**: FastAPI for API service
- **AWS Integration**: boto3 for S3 access and Bedrock
- **APIs**: CoinGecko API (live data) + S3 bucket (reproducible testing)

### Data Sources
- **S3 Bucket Strategy**:
  - **Instructor's Bucket**: `crypto-news-pdfs-sep-2025` (source of 15 PDFs via news_sources.json)
  - **Student's Bucket**: Each student creates their own S3 bucket for data storage
  - **Process**: Download PDFs from instructor's bucket → store in student's bucket → populate database
- **Live API**: CoinGecko API for real-time crypto news
  - Endpoint: `https://api.coingecko.com/api/v3/search/trending`
  - Rate limiting: 10-30 calls/minute (free tier)
  - **Note**: Free tier still requires API key

### Database Schema
```sql
-- News articles table (Day 1)
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
    s3_bucket_source VARCHAR(255), -- S3 bucket where article was sourced from
    s3_key_source VARCHAR(500), -- S3 key/path of the source file
    created_at TIMESTAMP DEFAULT NOW()
);

-- Note: Vector embeddings will be added in Day 3 with pgvector extension
```

### API Integration
- **S3 Integration**: Use boto3 to download PDFs from S3 bucket
- **FastAPI Service**: Create REST endpoints for CoinGecko news fetching
- **PDF Processing**: Extract text content from downloaded PDFs
- **Rate Limiting**: Handle CoinGecko API rate limits gracefully
- **Error Handling**: Graceful fallback between S3 and live API sources

### Sentiment Analysis
- Use Amazon Bedrock (Claude 3 Haiku) for sentiment classification
- Classify each article as: bullish, bearish, or neutral
- Include confidence score (0.0 to 1.0)
- Extract mentioned crypto tokens from article content

### Docker Setup
- **Container 1**: Python application (S3 fetcher + FastAPI + sentiment analysis)
- **Container 2**: PostgreSQL database with pgvector extension (cost-effective vs AWS RDS)
- **Docker Compose**: Orchestrate both containers
- **Environment variables**: AWS credentials, CoinGecko API key, database connection strings, S3 bucket configuration

### Environment Configuration
Create `.env` file with the following variables:
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/crypto_news
DB_NAME=crypto_news
DB_USER=user
DB_PASS=password

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration (Student's own bucket)
S3_BUCKET_NAME=your-student-bucket-name
S3_BUCKET_REGION=us-east-1

# CoinGecko API
COINGECKO_API_KEY=your_api_key_here

# Amazon Bedrock Configuration
AWS_BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
```

### Success Criteria
- [ ] Successfully download and process all 15 PDFs from S3 bucket
- [ ] Create FastAPI service with CoinGecko integration
- [ ] Parse and structure news data correctly (PDFs + API responses)
- [ ] Perform sentiment analysis using Amazon Bedrock
- [ ] Store data in PostgreSQL database
- [ ] Run entire stack with `docker compose up`
- [ ] Handle basic error cases (S3 failures, API rate limits, database connection issues)

### Deliverables
- Working Docker Compose setup with PostgreSQL + pgvector
- Python application with S3 PDF processing and FastAPI service
- PostgreSQL database with proper schema (including S3 source tracking)
- Environment configuration files (.env.example and .env)
- Basic logging and error handling
- README with setup instructions
- Test suite for S3 PDF processing (reproducible results)

### Storage Strategy
- **Local PostgreSQL**: Dockerized Postgres with pgvector extension (cost-effective vs AWS RDS)
- **S3 Source Tracking**: Store S3 bucket and key information for each article
- **Future-Ready**: Schema prepared for vector embeddings (Day 3)
- **Student Buckets**: Each student uses their own S3 bucket for data storage

