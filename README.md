# Crypto News & Sentiment Agent

### An Agentic AI Workflow for Crypto News Sentiment Analysis

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock access
- CoinGecko API key (free tier)
- Docker and Docker Compose
- Python 3.11+
- GitHub account for CI/CD

### 1. Setup GitHub Secrets (For Deployment)

Before deploying, add these secrets to your GitHub repository:

**Go to: Repository Settings → Secrets and variables → Actions → New repository secret**

#### Required Deployment Secrets:
```bash
# AWS & Infrastructure
AWS_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsDeployRole
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
EC2_HOST=your.ec2.public.ip
EC2_USER=ubuntu
EC2_SSH_KEY=<paste-your-private-ssh-key-content>

# Application Secrets
DB_PASS=your-secure-database-password
S3_BUCKET_NAME=your-s3-bucket-name
COINGECKO_API_KEY=your-coingecko-api-key-or-leave-empty
API_KEY=crypto-agent-secret-key

# Grafana Cloud Observability (for metrics visualization)
GRAFANA_CLOUD_PROMETHEUS_URL=https://prometheus-prod-XX-XXX.grafana.net/api/prom/push
GRAFANA_CLOUD_PROMETHEUS_USERNAME=your-grafana-username
GRAFANA_CLOUD_PROMETHEUS_PASSWORD=your-grafana-api-key
```

**📊 To get Grafana Cloud credentials:**
1. Create free account at: https://grafana.com/auth/sign-up
2. Go to: **Connections** → **Add new connection** → **Hosted Prometheus metrics**
3. Select: **"From my local Prometheus server"**
4. Copy the three values (url, username, password) shown in the configuration

**Note:** AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are NOT needed - the EC2 instance uses an IAM role for AWS access.

### 2. Setup Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials:
# - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# - S3_BUCKET_NAME (your own bucket)
# - COINGECKO_API_KEY
```

### 3. Start Services
```bash
# Start Docker containers
make up

# Initialize database
make setup

# Run tests to verify everything is working
make test
```

### 4. Use the API
```bash
# Test API endpoints
curl http://localhost:8000/health

# Process S3 PDFs (15 crypto news articles)
curl -X POST http://localhost:8000/api/process/s3/

# Fetch live news from CoinGecko
curl -X POST http://localhost:8000/api/fetch/live/

# Analyze sentiment using Amazon Bedrock
curl -X POST http://localhost:8000/api/analyze/sentiment/
```

## 🚢 Deployment

### Deploying to Production (EC2)

The project uses GitHub Actions for CI/CD. To deploy:

1. **Merge to production branch:**
```bash
git checkout production
git merge main
git push origin production
```

2. **GitHub Actions will automatically:**
   - Run tests and linting
   - Build Docker image
   - Push to Amazon ECR
   - Deploy to EC2 instance
   - **Run database migrations** (Alembic upgrade)
   - Run health checks

3. **Access your deployed application:**
```bash
curl http://YOUR_EC2_IP:8000/health
```

**Note:** Make sure all GitHub Secrets are configured (see Setup section above).

### Database Migrations

The deployment script automatically runs Alembic migrations. You can also run them manually:

```bash
# On EC2, run migrations manually if needed
docker-compose exec crypto-agent alembic upgrade head

# Check current migration version
docker-compose exec crypto-agent alembic current

# View migration history
docker-compose exec crypto-agent alembic history
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and available endpoints |
| `/health` | GET | Health check for Docker |
| `/metrics` | GET | Prometheus metrics (public, for scraping) |
| `/api/news/` | GET | Get news articles with filtering |
| `/api/sentiment/` | GET | Get sentiment analysis results |
| `/api/stats/` | GET | Database statistics |
| `/api/process/s3/` | POST | Process S3 PDFs |
| `/api/fetch/live/` | POST | Fetch live news from CoinGecko |
| `/api/analyze/sentiment/` | POST | Analyze sentiment for articles |
| `/api/embeddings/generate/` | POST | Generate embeddings for all articles (Day 3) |
| `/api/search/similar/{article_id}` | GET | Find similar articles using vector search (Day 3) |
| `/api/search/query` | POST | Search articles by natural language query (Day 3) |

### Example API Usage

**Note:** All API endpoints (except `/` and `/health`) require the `X-API-Key` header for authentication.

```bash
# Set your API key (default from env.example)
API_KEY="crypto-agent-secret-key"

# Get all news articles
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/news/

# Get bullish sentiment articles only
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/news/?sentiment=bullish"

# Get articles mentioning BTC
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/news/?token=BTC"

# Get sentiment analysis for BTC
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/sentiment/?token=BTC"

# Get database statistics
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/stats/

# Process S3 PDFs
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/api/process/s3/

# Fetch live news
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/api/fetch/live/

# Analyze sentiment
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/api/analyze/sentiment/

# Generate embeddings for all articles (Day 3)
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/api/embeddings/generate/

# Find similar articles (Day 3)
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/search/similar/1?limit=5"

# Search by natural language query (Day 3)
curl -X POST -H "X-API-Key: $API_KEY" "http://localhost:8000/api/search/query?query=Bitcoin%20price%20prediction&limit=10"
```

## 🏗️ Architecture

- **FastAPI**: Web framework and REST API
- **PostgreSQL + pgvector**: Database with vector embeddings for semantic search
- **Amazon Bedrock**:
  - Claude 3 Haiku for sentiment analysis
  - Titan Text Embeddings V2 for generating 1024-dim vectors
- **Prometheus + Grafana Cloud**: Metrics collection and visualization
- **Jaeger**: Distributed tracing and performance monitoring
- **OpenTelemetry**: Unified observability instrumentation
- **Docker**: Containerized deployment
- **boto3**: AWS SDK for S3 and Bedrock integration
- **CoinGecko API**: Live crypto news data

## 📁 Project Structure

```
src/
├── main.py                  # FastAPI application
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── metrics.py              # Prometheus metrics middleware
├── tracing.py              # OpenTelemetry tracing setup
└── services/
    ├── s3_processor.py     # S3 PDF processing
    ├── coingecko_service.py # CoinGecko API integration
    ├── sentiment_analyzer.py # Bedrock sentiment analysis
    └── embedding_service.py  # Bedrock Titan embeddings (Day 3)

observability/
├── prometheus.yml          # Prometheus config (generated from template)
├── prometheus.yml.template # Prometheus template with Grafana Cloud
├── grafana-api-performance-dashboard.json  # Grafana dashboard
├── GRAFANA_DASHBOARDS.md  # Dashboard setup guide
└── README.md              # Observability documentation

alembic/
└── versions/              # Database migrations
```

## 🔧 Development Commands

```bash
# Core commands
make help              # Show all available commands
make build             # Build Docker images
make up                # Start services
make down              # Stop services
make setup             # Initialize database
make test              # Run tests
make clean             # Clean up containers and volumes

# Database migrations
make migrate           # Run database migrations
make migrate-create    # Create new migration
make migrate-rollback  # Rollback last migration

# Day 3 - Embeddings & Observability
make generate-embeddings  # Generate embeddings for all articles
make setup-prometheus     # Generate Prometheus config with Grafana Cloud credentials

# Development tools
make logs              # View logs
make shell             # Shell into container
make lint              # Run code linting
make format            # Format code with black/isort
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

## Use api key generator to create an api key for your project:
https://codepen.io/corenominal/pen/rxOmMJ

