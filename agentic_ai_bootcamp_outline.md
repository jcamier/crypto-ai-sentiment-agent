# Five-Day On-Site Agentic AI Engineering Bootcamp: Crypto News & Sentiment Agent
## AWS + GitHub + Docker + Postgres/pgvector + Amazon Bedrock

## Project Overview: Crypto News & Sentiment Agent
**Concept:** Build an agent that fetches the latest crypto news (provided s3 buckets), generates embeddings, stores them in Postgres/pgvector, and classifies sentiment (bullish, bearish, neutral).

**Value:** Students learn how to connect agents to external APIs, use embeddings, apply guardrails, and deploy to production AWS infrastructure.

**Capstone:** Dashboard with trends per token (BTC, ETH, SOL) deployed on AWS with full observability.

**Prerequisite:** Familiarity with LLM's, software development, coding (Javascript & Python used in course), Git, an AWS account.

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
- **LLMs**: Local Ollama models (llama3.2:latest) for development, prepare for Amazon Bedrock migration.
- **Containers**: Docker & Docker Compose (all services run locally).
- **Code Hosting**: GitHub free accounts.
- **APIs**: CoinGecko API (free tier) for live data + S3 bucket for reproducible testing
    - https://docs.coingecko.com/
- **AWS Integration**: boto3 for S3 access to crypto news PDFs
- **Web Framework**: FastAPI for API service development


**Build:** "Crypto News Fetcher Agent" in a Docker container that:
- Downloads and processes 15 crypto news PDFs from S3 bucket (reproducible testing)
- Creates FastAPI service to fetch latest crypto news from CoinGecko API (real-time data)
- Parses and structures news data from both sources
- Basic sentiment classification using local LLM
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

## Day 3 – Embeddings, Sentiment Analysis & Observability
**Tools & AWS Services:**
- **Database**: Postgres with `pgvector` (Docker container on EC2).
- **Observability**: Prometheus + Grafana Cloud + Jaeger (Docker containers).
- **Tracing**: OpenTelemetry Collector → Jaeger (local) + CloudWatch (AWS).
- **Embeddings**: Prepare for Amazon Bedrock Titan embeddings (Day 4).

**Build:**
- Extend crypto news agent: generate embeddings for news articles using local models.
- Store embeddings in Postgres/pgvector with proper schema design.
- Implement sentiment classification (bullish/bearish/neutral) for crypto news.
- Add observability stack: Prometheus → Grafana Cloud, OTel → Jaeger.
- Collect p50/p95 latency metrics and trace crypto news processing pipeline.
- Create basic dashboard showing sentiment trends by token (BTC, ETH, SOL).

**Discussion:** Embedding schema design for crypto news, vector similarity search patterns, and observability best practices for agentic workflows.

---

## Day 4 – Amazon Bedrock Integration & Production Guardrails
**Tools & AWS Services:**
- **LLM Service**: Amazon Bedrock (Claude 3.5 Sonnet, Titan embeddings).
- **Guardrails**: Amazon Bedrock Guardrails + OPA-style allowlist rules.
- **Testing**: pytest + synthetic evaluation sets for crypto sentiment accuracy.
- **Workflow orchestration**: Add retry logic and fallback mechanisms.

**Build:**
- Migrate from local LLM to Amazon Bedrock for sentiment analysis.
- Implement Bedrock Guardrails to filter sensitive/unsafe content in crypto news.
- Add OPA-style allowlist rules for crypto news API calls and sentiment classifications.
- Implement retry logic with exponential backoff for API failures.
- Add fallback LLM routing (Claude → Llama) for resilience.
- Create evaluation harness: test sentiment accuracy against gold dataset.
- Add I/O validation with Pydantic schemas for all LLM outputs.

**Discussion:** Balancing speed, safety, and cost in enterprise deployments; Bedrock pricing optimization strategies.

---

## Day 5 – Capstone: Production Crypto Sentiment Dashboard
**Team Project:** Complete crypto news & sentiment agent with production dashboard.

**Use case**: Crypto news ingestion → sentiment analysis with Bedrock → embedding storage in Postgres/pgvector → real-time dashboard with trends per token (BTC, ETH, SOL).

**Must include:**
- **CI/CD Pipeline**: GitHub Actions with OIDC → AWS IAM role
- **AWS Infrastructure**: EC2 + ECR + SSM Parameter Store + CloudFront
- **Database**: Postgres/pgvector with crypto news embeddings
- **LLM Integration**: Amazon Bedrock (Claude 3.5 Sonnet + Titan embeddings)
- **Security**: Bedrock Guardrails + OPA allowlist rules + IAM least-privilege
- **Observability**: Prometheus → Grafana Cloud + OTel → Jaeger + CloudWatch
- **Resilience**: Retry logic + fallback LLM routing + evaluation harness
- **Dashboard**: Real-time crypto sentiment trends by token with historical data

**Production Deployment:**
- Deploy to AWS EC2 with CloudFront edge distribution
- Configure security groups (public web access, private database/observability)
- Set up monitoring alerts for API failures and sentiment accuracy drift
- Implement canary deployment for model updates

**Closing:**
- Teams present architecture choices and demo live crypto sentiment dashboard.
- Instructor demo: enterprise scaling patterns (RDS, ElastiCache, multi-region deployment).
- Deliverable: full GitHub repo with AWS infrastructure, CI/CD workflows, and production-ready crypto sentiment agent.
