# Five-Day On-Site Agentic AI Engineering Bootcamp: Crypto News & Sentiment Agent
## AWS + GitHub + Docker + Postgres/pgvector + Amazon Bedrock

## Project Overview: Crypto News & Sentiment Agent
**Concept:** Build an agent that fetches the latest crypto news (provided s3 buckets), generates embeddings, stores them in Postgres/pgvector, and classifies sentiment (bullish, bearish, neutral).

**Value:** Students learn how to connect agents to external APIs, use embeddings, apply guardrails, and deploy to production AWS infrastructure.

**Capstone:** Dashboard with trends per token (BTC, ETH, SOL) deployed on AWS with full observability.

**Prerequisite:** Familiarity with LLM's, software development, coding, debugging, Python, Git, an AWS account.

## Format
- **Morning:** principles + live demo
- **Midday:** guided hands-on build
- **Afternoon:** breakout discussions & debugging support
- **Project:** cumulative build → production-grade crypto sentiment agent deployed on AWS by Day 5

---

## Day 1 – Foundations & Crypto News Integration
**Tools & Free Options:**
- Using AI-native coding tools (Cursor, Claude Code, Opencode.ai)
    - https://cursor.com/
    - https://opencode.ai/
    - https://claude.com/product/claude-code
- Spec-Driven AI Development
- **LLMs**: Amazon Bedrock (Claude 3 Haiku) for cost-effective sentiment analysis and embeddings.
- **Containers**: Docker & Docker Compose (all services run locally).
  - **Note**: For production, consider Podman for better security (rootless containers)
- **Code Hosting**: GitHub free accounts.
- **APIs**: CoinGecko API (free tier) for live data + S3 bucket for reproducible testing
    - https://docs.coingecko.com/
- **AWS Integration**: boto3 for S3 access to crypto news PDFs
- **Web Framework**: FastAPI for API service development


**Build:** "Crypto News Fetcher Agent" in a Docker container that:
- Downloads and processes 15 crypto news PDFs from S3 bucket (reproducible testing)
- Creates FastAPI service to fetch latest crypto news from CoinGecko API (real-time data)
- Parses and structures news data from both sources
- Basic sentiment classification using Amazon Bedrock
- Stores processed data in local Postgres container

**Discussion:** API rate limits, data quality, and what happens in production when scaling, auth, and retries are needed.

---

## Day 2 – AWS Infrastructure & CI/CD Pipeline
**Tools & AWS Services:**
- **AWS Account Setup**: EC2 (t4g.large), ECR, IAM roles, SSM Parameter Store.
- **CI/CD**: GitHub Actions with OIDC → AWS IAM role (no GitHub Secrets).
- **Container Registry**: Amazon ECR for storing Docker images.
- **Secrets Management**: AWS SSM Parameter Store for runtime secrets.

**Build:**
- Set up AWS infrastructure (EC2 instance, ECR repository, IAM roles).
- Create GitHub Actions pipeline with OIDC authentication to AWS.
- Build & push Docker images to ECR (agent service + Postgres with pgvector).
- Using Terraform on AWS to deploy with Github
- Deploy initial crypto news agent to EC2 using Docker Compose.
- Store API keys in SSM Parameter Store, retrieve at runtime.

**Discussion:** OIDC vs GitHub Secrets, IAM least-privilege principles, and enterprise security patterns.

---

## Day 3 – Embeddings, Vector Storage & Observability
**Tools & AWS Services:**
- **Database**: Postgres with `pgvector` extension (Docker container on EC2).
- **Embeddings**: Amazon Bedrock Titan Text Embeddings for semantic search.
- **Observability**: Prometheus + Grafana Cloud + Jaeger (Docker containers).
- **Tracing**: OpenTelemetry Collector → Jaeger (local) + CloudWatch (AWS).
- **Metrics**: Application metrics, API latency, sentiment distribution.

**Build:**
- Integrate Amazon Bedrock Titan embeddings for crypto news articles.
- Design and implement pgvector schema for efficient embedding storage.
- Add vector similarity search endpoints (find semantically similar news).
- Enhance sentiment analysis with Bedrock (ensure full coverage of news sources).
- Deploy full observability stack: Prometheus → Grafana Cloud, OTel → Jaeger.
- Instrument application with custom metrics: API latency (p50/p95/p99), embedding generation time.
- Create Grafana dashboards showing sentiment trends by token (BTC, ETH, SOL) with historical data.
- Add distributed tracing for full request lifecycle (S3 → embeddings → sentiment → storage).

**Discussion:** Vector database schema design for production, semantic search patterns for crypto news, observability best practices for LLM workflows, and cost optimization for Bedrock embeddings.

---

## Day 4 – Guardrails, Evaluation & Production Resilience
**Tools & AWS Services:**
- **Guardrails**: Amazon Bedrock Guardrails for content filtering and topic detection.
- **Security**: Prompt injection protection and input validation.
- **Testing**: pytest + synthetic evaluation datasets for sentiment accuracy.
- **Resilience**: Retry logic, circuit breakers, and fallback mechanisms.
- **Monitoring**: Cost tracking and rate limit management for Bedrock.

**Build:**
- Implement Amazon Bedrock Guardrails for content filtering (sensitive topics, harmful content).
- Add guardrails for topic detection (ensure content is crypto-related).
- Build prompt injection protection for sentiment analysis inputs.
- Create evaluation harness with gold dataset (100+ labeled crypto news samples).
- Implement sentiment accuracy metrics and confusion matrix tracking.
- Add retry logic with exponential backoff and jitter for API failures.
- Implement circuit breaker pattern for Bedrock API calls.
- Add fallback mechanisms (Claude Sonnet → Haiku, cached responses on failure).
- Build synthetic test suite for edge cases (rate limits, API errors, malformed inputs).
- Add cost monitoring dashboard: track Bedrock API costs per endpoint.
- Implement rate limit handling and request throttling.

**Discussion:** Balancing speed, safety, and cost in production LLM systems; evaluation methodologies for sentiment analysis; building resilient agentic workflows.

---

## Day 5 – Capstone: Production Crypto Sentiment Dashboard
**Team Project:** Polish and integrate all components into production-ready crypto sentiment dashboard.

**Use case**: End-to-end crypto intelligence platform - News ingestion (S3 + CoinGecko) → Bedrock sentiment analysis → Titan embeddings → pgvector storage → semantic search → real-time dashboard with trends per token (BTC, ETH, SOL).

**Integration Tasks:**
- **Polish Dashboard UI**: Create production-quality Streamlit or React dashboard
- **Add Advanced Features**:
  - Semantic search for similar news articles (using pgvector similarity)
  - Sentiment trend visualization by token over time
  - News source reliability scoring
  - Alert system for significant sentiment shifts
- **Performance Optimization**:
  - Implement caching strategy (Redis) for frequent queries
  - Optimize pgvector indexes for fast similarity search
  - Add connection pooling for database
- **Production Hardening**:
  - Add comprehensive error handling and logging
  - Implement health checks for all services
  - Add automated smoke tests for deployment validation
  - Configure alerts for system failures and accuracy drift

**Production Deployment Checklist:**
- ✅ **CI/CD Pipeline**: GitHub Actions with OIDC → AWS IAM role
- ✅ **AWS Infrastructure**: EC2 + ECR + IAM roles + Security Groups
- ✅ **Database**: Postgres/pgvector with embeddings and proper indexes
- ✅ **LLM Integration**: Amazon Bedrock (Claude Haiku for sentiment + Titan for embeddings)
- ✅ **Security**: API key authentication + Bedrock Guardrails + IAM least-privilege
- ✅ **Observability**: Prometheus → Grafana Cloud + OTel → Jaeger + custom dashboards
- ✅ **Resilience**: Retry logic + circuit breakers + fallback mechanisms + evaluation harness
- ✅ **Dashboard**: Real-time sentiment trends, semantic search, and news analytics

**Final Presentation:**
- Each team presents their architecture decisions and trade-offs
- Live demo of crypto sentiment dashboard with real-time data
- Discussion of lessons learned and production challenges faced
- Instructor demo: Enterprise scaling patterns (RDS, ElastiCache, multi-region, auto-scaling)

**Deliverables:**
- Full GitHub repository with complete source code
- AWS infrastructure deployed and running
- CI/CD pipeline with automated testing
- Grafana dashboards showing system health and sentiment metrics
- Documentation for deployment and operations
- Evaluation results and accuracy metrics
