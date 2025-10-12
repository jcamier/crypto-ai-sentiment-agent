# Crypto News & Sentiment Agent - Day 3 Specification

## Project Overview
Integrate Amazon Bedrock Titan embeddings for semantic search, implement pgvector for efficient vector storage, and deploy comprehensive observability with Prometheus, Grafana Cloud, and Jaeger for distributed tracing.

## Why This Approach?
Day 3 focuses on **production-grade semantic search** and **complete observability** that are essential for any AI-powered application:

### Semantic Search & Embeddings
- **Vector Embeddings**: Transform text into numerical representations for semantic similarity
- **Amazon Bedrock Titan**: Production-ready embeddings without managing infrastructure
- **pgvector Extension**: Efficient vector similarity search directly in PostgreSQL
- **Similarity Search**: Find semantically related articles, not just keyword matches

### Observability Stack
- **Prometheus**: Industry-standard metrics collection and alerting
- **Grafana Cloud**: Centralized dashboards with zero infrastructure management
- **Jaeger**: Distributed tracing for complex request flows
- **OpenTelemetry**: Unified observability instrumentation standard

### Production Readiness
- **Performance Metrics**: Track API latency (p50/p95/p99) for SLA monitoring
- **Cost Tracking**: Monitor Bedrock API usage and embedding generation costs
- **Error Tracking**: Identify and debug issues in production quickly
- **User Experience**: Understand system behavior from user perspective

## Prerequisites: AWS Bedrock Access

**⚠️ IMPORTANT: Ensure Amazon Bedrock access before proceeding**

### Required AWS Permissions:
1. **Bedrock Model Access**: Enable Titan Text Embeddings in Bedrock console
2. **IAM Permissions**: Update IAM roles to include Bedrock embedding access
3. **Cost Monitoring**: Set up billing alerts for Bedrock usage

### Bedrock Model Requirements:
- **Embedding Model**: `amazon.titan-embed-text-v2` (1024 dimensions)
- **Region**: Ensure Bedrock is available in your deployment region (us-east-1 recommended)
- **Quotas**: Check service quotas for embedding generation rate limits

### Setup Steps:
1. Enable Bedrock Titan embeddings in AWS Console
2. Update IAM policies with Bedrock embedding permissions
3. Test embedding generation with sample text
4. Configure cost alerts for Bedrock usage

**Note**: Without Bedrock access, embedding generation will fail.

## Day 3 Requirements

### Core Functionality
- **Titan Embeddings Integration**: Use Amazon Bedrock to generate embeddings for all news articles
- **pgvector Schema**: Design and implement efficient vector storage in PostgreSQL
- **Semantic Search API**: Create endpoints for finding similar articles by content
- **Enhanced Sentiment**: Ensure all articles have sentiment analysis coverage
- **Observability Stack**: Deploy Prometheus, Grafana Cloud, and Jaeger
- **Custom Metrics**: Instrument application with latency, throughput, and error metrics
- **Distributed Tracing**: Add OpenTelemetry tracing for full request lifecycle

### Technical Stack
- **Embeddings**: Amazon Bedrock Titan Text Embeddings
- **Vector Database**: PostgreSQL with pgvector extension
- **Metrics**: Prometheus + Grafana Cloud
- **Tracing**: OpenTelemetry + Jaeger (local) + CloudWatch (AWS)
- **Instrumentation**: prometheus-client, opentelemetry-api, opentelemetry-sdk
- **Dashboards**: Grafana Cloud for visualization

### Database Schema Updates

#### Add Vector Embeddings Column
```sql
-- Add pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to news_articles table
ALTER TABLE news_articles
ADD COLUMN embedding vector(1024);  -- Titan v2 generates 1024-dimensional vectors

-- Create index for fast similarity search
CREATE INDEX ON news_articles USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- For better performance with more data, consider HNSW index:
-- CREATE INDEX ON news_articles USING hnsw (embedding vector_cosine_ops);
```

#### Updated Schema
```sql
-- Complete news_articles table (Day 3)
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(255),
    url TEXT,
    published_at TIMESTAMP,
    tokens_mentioned JSON, -- Array of crypto tokens mentioned
    sentiment VARCHAR(20), -- bullish, bearish, neutral
    confidence_score FLOAT,
    s3_bucket_source VARCHAR(255), -- S3 bucket where article was sourced from
    s3_key_source VARCHAR(500), -- S3 key/path of the source file
    embedding vector(1024), -- Titan v2 embedding vector
    embedding_model VARCHAR(100), -- Track which model generated the embedding
    embedding_generated_at TIMESTAMP, -- When embedding was created
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sentiment ON news_articles(sentiment);
CREATE INDEX idx_tokens ON news_articles USING GIN(tokens_mentioned);
CREATE INDEX idx_source ON news_articles(source);
CREATE INDEX idx_published ON news_articles(published_at DESC);
CREATE INDEX idx_embedding ON news_articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Amazon Bedrock Titan Integration

#### Embedding Service Implementation
```python
# src/services/embedding_service.py
import boto3
import json
import logging
from typing import List, Dict, Any
from decouple import config

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using Amazon Bedrock Titan."""

    def __init__(self):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=config('AWS_BEDROCK_REGION', default='us-east-1')
        )
        self.model_id = config(
            'BEDROCK_EMBEDDING_MODEL_ID',
            default='amazon.titan-embed-text-v2'
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.

        Args:
            text: Text to embed (max 8K tokens for Titan v2)

        Returns:
            List of floats representing the embedding vector (1024 dimensions)
        """
        try:
            # Truncate text if too long (rough estimate: 1 token ≈ 4 chars)
            max_chars = 25000  # Conservative limit for 8K tokens
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Truncated text to {max_chars} characters")

            # Prepare request body
            body = json.dumps({
                "inputText": text
            })

            # Call Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')

            if not embedding:
                raise ValueError("No embedding returned from Bedrock")

            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Titan doesn't support batch API, so we call individually.
        Consider implementing rate limiting and retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                logger.info(f"Generated embedding {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i+1}: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 1024)

        return embeddings
```

#### Update Sentiment Analyzer to Include Embeddings
```python
# src/services/sentiment_analyzer.py (updated)
from src.services.embedding_service import EmbeddingService

class SentimentAnalyzer:
    def __init__(self):
        self.bedrock_client = boto3.client(...)
        self.embedding_service = EmbeddingService()

    def analyze_with_embedding(self, article_id: int, content: str, db: Session):
        """Analyze sentiment and generate embedding for article."""
        # Generate sentiment (existing code)
        sentiment_result = self.analyze_sentiment(content)

        # Generate embedding
        embedding = self.embedding_service.generate_embedding(content)

        # Update database
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if article:
            article.sentiment = sentiment_result['sentiment']
            article.confidence_score = sentiment_result['confidence']
            article.embedding = embedding
            article.embedding_model = 'amazon.titan-embed-text-v2'
            article.embedding_generated_at = datetime.utcnow()
            db.commit()
```

### Semantic Search API Endpoints

#### Vector Similarity Search
```python
# src/main.py (add new endpoints)

@app.get("/api/search/similar/")
@limiter.limit("10/minute")
async def search_similar_articles(
    request: Request,
    api_key: str = Depends(verify_api_key),
    article_id: int = Query(..., description="ID of the article to find similar articles for"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Find articles similar to the given article using vector similarity.
    Uses cosine similarity on embeddings.
    """
    try:
        # Get the reference article
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article or not article.embedding:
            raise HTTPException(status_code=404, detail="Article not found or has no embedding")

        # Find similar articles using pgvector
        # Use cosine distance (1 - cosine_similarity) for similarity search
        similar_articles = db.query(
            NewsArticle.id,
            NewsArticle.title,
            NewsArticle.source,
            NewsArticle.published_at,
            NewsArticle.sentiment,
            NewsArticle.embedding.cosine_distance(article.embedding).label('distance')
        ).filter(
            NewsArticle.id != article_id,
            NewsArticle.embedding.isnot(None)
        ).order_by(
            NewsArticle.embedding.cosine_distance(article.embedding)
        ).limit(limit).all()

        return {
            "reference_article": {
                "id": article.id,
                "title": article.title,
                "source": article.source
            },
            "similar_articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "source": a.source,
                    "published_at": a.published_at,
                    "sentiment": a.sentiment,
                    "similarity_score": 1 - a.distance  # Convert distance to similarity
                }
                for a in similar_articles
            ]
        }
    except Exception as e:
        logger.error(f"Error finding similar articles: {e}")
        raise HTTPException(status_code=500, detail="Error performing similarity search")


@app.post("/api/search/semantic/")
@limiter.limit("10/minute")
async def semantic_search(
    request: Request,
    api_key: str = Depends(verify_api_key),
    query: str = Query(..., description="Search query text"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Perform semantic search across all articles using natural language query.
    Generates embedding for query and finds similar articles.
    """
    try:
        # Generate embedding for search query
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.generate_embedding(query)

        # Find similar articles
        results = db.query(
            NewsArticle.id,
            NewsArticle.title,
            NewsArticle.content,
            NewsArticle.source,
            NewsArticle.published_at,
            NewsArticle.sentiment,
            NewsArticle.tokens_mentioned,
            NewsArticle.embedding.cosine_distance(query_embedding).label('distance')
        ).filter(
            NewsArticle.embedding.isnot(None)
        ).order_by(
            NewsArticle.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()

        return {
            "query": query,
            "results": [
                {
                    "id": r.id,
                    "title": r.title,
                    "content": r.content[:200] + "..." if r.content else None,
                    "source": r.source,
                    "published_at": r.published_at,
                    "sentiment": r.sentiment,
                    "tokens_mentioned": r.tokens_mentioned,
                    "relevance_score": 1 - r.distance
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise HTTPException(status_code=500, detail="Error performing semantic search")


@app.post("/api/embeddings/generate/")
@limiter.limit("5/minute")
async def generate_embeddings_for_all(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Generate embeddings for all articles that don't have them yet.
    This is a background task that can take several minutes.
    """
    try:
        # Get articles without embeddings
        articles = db.query(NewsArticle).filter(
            NewsArticle.embedding.is_(None)
        ).all()

        if not articles:
            return {"message": "All articles already have embeddings", "count": 0}

        embedding_service = EmbeddingService()
        processed = 0

        for article in articles:
            try:
                # Combine title and content for embedding
                text = f"{article.title}\n\n{article.content or ''}"
                embedding = embedding_service.generate_embedding(text)

                article.embedding = embedding
                article.embedding_model = 'amazon.titan-embed-text-v2'
                article.embedding_generated_at = datetime.utcnow()
                db.commit()

                processed += 1
                logger.info(f"Generated embedding for article {article.id}")

            except Exception as e:
                logger.error(f"Failed to generate embedding for article {article.id}: {e}")
                continue

        return {
            "message": "Embeddings generated successfully",
            "total_articles": len(articles),
            "processed": processed
        }

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail="Error generating embeddings")
```

### Observability Stack Setup

#### Docker Compose Updates
```yaml
# docker-compose.yml (add observability services)
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    # ... existing db config ...

  crypto-agent:
    build: .
    # ... existing app config ...
    environment:
      # ... existing env vars ...
      - PROMETHEUS_ENABLED=true
      - JAEGER_ENABLED=true
      - OTEL_SERVICE_NAME=crypto-sentiment-agent
      - OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "5775:5775/udp"   # Agent - accept zipkin.thrift over compact thrift protocol
      - "6831:6831/udp"   # Agent - accept jaeger.thrift over compact thrift protocol
      - "6832:6832/udp"   # Agent - accept jaeger.thrift over binary thrift protocol
      - "5778:5778"       # Agent - serve configs
      - "16686:16686"     # Query - serve frontend
      - "14250:14250"     # Collector - accept model.proto
      - "14268:14268"     # Collector - accept jaeger.thrift directly from clients
      - "14269:14269"     # Collector - health check
      - "9411:9411"       # Collector - Zipkin compatible endpoint
      - "4317:4317"       # OTLP gRPC receiver
      - "4318:4318"       # OTLP HTTP receiver
    restart: unless-stopped

volumes:
  postgres_data:
  prometheus_data:
```

#### Prometheus Configuration
```yaml
# observability/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'crypto-sentiment-agent'
    environment: 'production'

# Grafana Cloud Remote Write (optional)
remote_write:
  - url: https://prometheus-prod-XX-XXX.grafana.net/api/prom/push
    basic_auth:
      username: YOUR_GRAFANA_CLOUD_USERNAME
      password: YOUR_GRAFANA_CLOUD_API_KEY

scrape_configs:
  - job_name: 'crypto-agent'
    static_configs:
      - targets: ['crypto-agent:8000']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### Application Metrics Instrumentation
```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Business metrics
articles_processed_total = Counter(
    'articles_processed_total',
    'Total articles processed',
    ['source']
)

sentiment_analysis_total = Counter(
    'sentiment_analysis_total',
    'Total sentiment analyses',
    ['sentiment']
)

embedding_generation_duration_seconds = Histogram(
    'embedding_generation_duration_seconds',
    'Time to generate embeddings',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

bedrock_api_calls_total = Counter(
    'bedrock_api_calls_total',
    'Total Bedrock API calls',
    ['model', 'operation', 'status']
)

bedrock_api_cost_usd = Counter(
    'bedrock_api_cost_usd',
    'Estimated Bedrock API cost in USD',
    ['model', 'operation']
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

vector_search_duration_seconds = Histogram(
    'vector_search_duration_seconds',
    'Time to perform vector similarity search',
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)


# Middleware for automatic request tracking
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Add middleware to app
app.add_middleware(MetricsMiddleware)
```

#### OpenTelemetry Tracing Setup
```python
# src/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import logging

logger = logging.getLogger(__name__)


def setup_tracing(app, service_name="crypto-sentiment-agent"):
    """
    Configure OpenTelemetry tracing with Jaeger exporter.
    """
    try:
        # Create resource with service name
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": "production"
        })

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )

        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()

        # Instrument requests library
        RequestsInstrumentor().instrument()

        logger.info("OpenTelemetry tracing configured successfully")

    except Exception as e:
        logger.error(f"Failed to set up tracing: {e}")


# Update src/main.py to enable tracing
from src.tracing import setup_tracing

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    try:
        init_db()
        setup_pgvector()
        setup_tracing(app)  # Add tracing setup
        logger.info("Database and tracing initialized successfully")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Application shutting down")
```

### Dependencies Update
```toml
# pyproject.toml (add new dependencies)
dependencies = [
    # ... existing dependencies ...

    # Observability
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "opentelemetry-instrumentation-sqlalchemy>=0.41b0",
    "opentelemetry-instrumentation-requests>=0.41b0",
    "opentelemetry-exporter-jaeger>=1.20.0",
    "opentelemetry-exporter-jaeger-thrift>=1.20.0",
]
```

### Grafana Cloud Setup

#### Create Dashboards
1. **API Performance Dashboard**:
   - HTTP request rate (requests/sec)
   - Request latency (p50, p95, p99)
   - Error rate by endpoint
   - Request distribution by method

2. **Business Metrics Dashboard**:
   - Articles processed by source
   - Sentiment distribution (bullish/bearish/neutral)
   - Embedding generation rate
   - Semantic search usage

3. **Bedrock Cost Dashboard**:
   - API calls by model
   - Estimated cost by operation
   - Cost per article processed
   - Daily/weekly/monthly cost trends

4. **Database Performance Dashboard**:
   - Active connections
   - Query duration
   - Vector search latency
   - Cache hit rate

### Environment Configuration Updates
```bash
# .env (add observability config)

# Observability
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
OTEL_SERVICE_NAME=crypto-sentiment-agent
OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces

# Grafana Cloud (optional - for remote write)
GRAFANA_CLOUD_URL=https://prometheus-prod-XX-XXX.grafana.net/api/prom/push
GRAFANA_CLOUD_USERNAME=your_username
GRAFANA_CLOUD_API_KEY=your_api_key
```

### Success Criteria
- [ ] Successfully integrate Amazon Bedrock Titan embeddings
- [ ] Update database schema with pgvector column and indexes
- [ ] Generate embeddings for all existing articles
- [ ] Implement semantic search endpoints (similar articles, query search)
- [ ] Deploy Prometheus and Jaeger containers
- [ ] Configure Grafana Cloud integration
- [ ] Create comprehensive dashboards (API, business, cost, database)
- [ ] Instrument application with custom metrics
- [ ] Add distributed tracing with OpenTelemetry
- [ ] Test vector similarity search performance
- [ ] Verify observability data flow (metrics → Grafana, traces → Jaeger)
- [ ] Document embedding model and search patterns

### Deliverables
- **Embedding Service**: Amazon Bedrock Titan integration
- **Vector Database**: pgvector schema with efficient indexes
- **Semantic Search API**: Two new endpoints for similarity search
- **Prometheus Setup**: Metrics collection and scraping
- **Jaeger Setup**: Distributed tracing infrastructure
- **Grafana Dashboards**: Four comprehensive dashboards
- **OpenTelemetry Instrumentation**: Automatic tracing for all requests
- **Custom Metrics**: Business and technical metrics
- **Performance Tests**: Vector search benchmark results
- **Documentation**: Observability setup and dashboard guides

### Cost Optimization
- **Bedrock Embeddings**: Titan v2 ($0.00002 per 1K tokens input-only)
  - Average article: ~500 tokens = $0.00001 per article
  - 100 articles/day = $0.001/day = ~$0.03/month
- **Vector Storage**: Minimal incremental cost (~4KB per embedding)
- **Observability**: Grafana Cloud free tier (10K series, 50GB logs/month)
- **Jaeger**: Self-hosted (minimal resource usage)
- **Total Incremental Cost**: ~$1-2/month for embeddings

### Performance Benchmarks

#### Expected Performance Targets
- **Embedding Generation**: < 2 seconds per article
- **Vector Similarity Search**: < 100ms for top-10 results
- **Semantic Search Query**: < 500ms end-to-end
- **API Response Time (p95)**: < 1 second
- **Database Query Time**: < 50ms average

#### pgvector Index Performance
```sql
-- Test query performance (should return in < 100ms with proper index)
EXPLAIN ANALYZE
SELECT id, title, embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM news_articles
WHERE embedding IS NOT NULL
ORDER BY distance
LIMIT 10;
```

### Troubleshooting Guide

#### Common Issues

1. **Bedrock Embedding Failures**
   - Verify model access in Bedrock console
   - Check IAM permissions for `bedrock:InvokeModel`
   - Ensure text length is within limits (8K tokens for Titan v1)
   - Monitor throttling errors and implement backoff

2. **pgvector Performance Issues**
   - Verify index creation: `\d+ news_articles`
   - Rebuild index if needed: `REINDEX INDEX news_articles_embedding_idx;`
   - Consider HNSW index for better performance at scale
   - Adjust `lists` parameter based on data size

3. **Prometheus Scraping Failures**
   - Check `/metrics` endpoint accessibility
   - Verify prometheus.yml configuration
   - Ensure network connectivity between containers
   - Check for firewall/security group issues

4. **Jaeger Trace Collection Issues**
   - Verify Jaeger endpoint configuration
   - Check OpenTelemetry instrumentation setup
   - Ensure correct service name and tags
   - Validate span export settings

5. **Grafana Cloud Connection**
   - Verify remote_write credentials
   - Check API key permissions
   - Test connectivity to Grafana Cloud
   - Monitor remote_write queue metrics

### Next Steps (Day 4 Preview)
- **Bedrock Guardrails**: Add content filtering and safety checks
- **Evaluation Harness**: Test sentiment accuracy with gold dataset
- **Resilience Patterns**: Implement retry logic and circuit breakers
- **Cost Monitoring**: Track and optimize Bedrock API costs
- **Advanced Search**: Add filters and ranking to semantic search

### Resources
- [Amazon Bedrock Titan Embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Cloud Documentation](https://grafana.com/docs/grafana-cloud/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)

