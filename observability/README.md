# Observability Stack

This directory contains configuration for the observability stack used in the Crypto Sentiment Agent.

## Components

### Prometheus
- **Purpose**: Metrics collection and storage
- **Port**: 9090
- **Config**: `prometheus.yml`
- **Access**: http://localhost:9090

### Jaeger
- **Purpose**: Distributed tracing
- **UI Port**: 16686
- **Collector Port**: 14268
- **Access**: http://localhost:16686

### Grafana Cloud (Optional)
- **Purpose**: Centralized metrics visualization
- **Setup**: Uncomment `remote_write` section in `prometheus.yml`
- **Free Tier**: 10K series, 50GB logs/month

## Configuration

### prometheus.yml
Main Prometheus configuration file that defines:
- **Scrape targets**: What services to collect metrics from
- **Scrape intervals**: How often to collect metrics (15s default)
- **Remote write**: Optional Grafana Cloud integration

### Scrape Jobs

1. **crypto-agent** (port 8000)
   - Application metrics
   - API performance
   - Business metrics
   - Bedrock API costs

2. **prometheus** (port 9090)
   - Prometheus self-monitoring
   - Storage metrics
   - Scrape health

## Metrics Exposed

### Application Metrics (`/metrics` endpoint)

**HTTP Metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram (p50/p95/p99)

**Business Metrics:**
- `articles_processed_total` - Total articles processed by source
- `sentiment_analysis_total` - Total sentiment analyses by sentiment
- `embedding_generation_duration_seconds` - Embedding generation time

**Bedrock Metrics:**
- `bedrock_api_calls_total` - Total Bedrock API calls by model/operation
- `bedrock_api_cost_usd` - Estimated Bedrock costs

**Database Metrics:**
- `db_connections_active` - Active database connections
- `vector_search_duration_seconds` - Vector similarity search latency

## Usage

### View Metrics Locally
```bash
# Start observability stack
docker compose up -d prometheus jaeger

# Access Prometheus UI
open http://localhost:9090

# Access Jaeger UI
open http://localhost:16686

# View raw metrics
curl http://localhost:8000/metrics
```

### Query Examples

**Prometheus Queries:**
```promql
# Request rate (per second)
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Bedrock API cost per hour
rate(bedrock_api_cost_usd[1h]) * 3600
```

### Grafana Cloud Setup (Optional)

1. Create free account at https://grafana.com/auth/sign-up
2. Get Prometheus remote write URL and credentials
3. Update `prometheus.yml` remote_write section
4. Restart Prometheus: `docker compose restart prometheus`

## Troubleshooting

### Metrics not appearing?
- Check if `/metrics` endpoint is accessible: `curl http://localhost:8000/metrics`
- Verify Prometheus can reach crypto-agent: Check Prometheus targets page
- Check Prometheus logs: `docker compose logs prometheus`

### Jaeger traces not showing?
- Verify OTEL_EXPORTER_JAEGER_ENDPOINT is set correctly
- Check Jaeger collector logs: `docker compose logs jaeger`
- Ensure OpenTelemetry is initialized in the application

### High cardinality warnings?
- Avoid using high-cardinality labels (e.g., user IDs, article IDs)
- Use exemplars instead of labels for high-cardinality data
- Configure metric relabeling if needed

## References
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Cloud](https://grafana.com/docs/grafana-cloud/)

