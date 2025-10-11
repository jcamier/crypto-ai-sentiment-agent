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
- **Purpose**: Centralized metrics visualization and dashboards
- **Setup**: Follow the Grafana Cloud Setup section below
- **Free Tier**: 10K series, 50GB logs/month
- **Benefit**: Persistent metrics storage and advanced visualization

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

### Grafana Cloud Setup - Secure Configuration

**Step 1: Get Your Grafana Cloud Credentials**
1. Create a free account at: https://grafana.com/auth/sign-up
2. Go to: **Connections** → **Add new connection** → **Hosted Prometheus metrics**
3. Select: **"From my local Prometheus server"**
4. Copy the three values from the configuration shown:
   - `url` → Save as GRAFANA_CLOUD_PROMETHEUS_URL
   - `username` → Save as GRAFANA_CLOUD_PROMETHEUS_USERNAME
   - `password` → Save as GRAFANA_CLOUD_PROMETHEUS_PASSWORD

**Step 2: Add Credentials to Your `.env` File**
```bash
# Add these lines to your .env file (NOT .env.example!)
# Replace the values with your actual Grafana Cloud credentials from Step 1
GRAFANA_CLOUD_PROMETHEUS_URL=https://prometheus-prod-XX-XXX.grafana.net/api/prom/push
GRAFANA_CLOUD_PROMETHEUS_USERNAME=your-username-here
GRAFANA_CLOUD_PROMETHEUS_PASSWORD=your-api-key-here
```

**Step 3: Generate Prometheus Config with Credentials**
```bash
# This command reads .env and generates observability/prometheus.yml
make setup-prometheus

# The generated file is gitignored (contains secrets)
```

**Step 4: Start the Stack and Verify**
```bash
# Start all services
make up

# Check Prometheus logs for successful remote write
docker compose logs prometheus | grep -i "remote_write"

# Visit your Grafana Cloud instance
# Go to Explore → Select "Prometheus" → Query: up{job="crypto-agent"}
```

**⚠️ Security Notes:**
- ✅ `observability/prometheus.yml` is gitignored (contains secrets)
- ✅ `observability/prometheus.yml.template` is the safe template (no secrets)
- ✅ Credentials come from `.env` (also gitignored)
- ✅ For production/GitHub: Add GRAFANA_CLOUD_* variables to GitHub Secrets
- ❌ NEVER commit actual credentials to git

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

