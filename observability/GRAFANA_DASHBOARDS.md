# Grafana Dashboards Setup Guide

This guide explains how to import and use the pre-configured Grafana dashboards for the Crypto Sentiment Agent.

## Available Dashboards

### 1. API Performance Dashboard
**File:** `grafana-api-performance-dashboard.json`

**Metrics:**
- **Request Rate**: Real-time requests per second by endpoint and method
- **Error Rate**: Percentage of 5xx errors with alerting (threshold: 5%)
- **Request Latency**: p50, p95, p99 latency percentiles
- **Status Code Distribution**: Breakdown of responses by HTTP status
- **Top Endpoints**: Most frequently called endpoints
- **Slowest Endpoints**: Endpoints with highest p95 latency
- **24-hour Summary**: Total requests, avg response time, error count, success rate

**Use Cases:**
- Monitor API health and performance
- Identify slow endpoints that need optimization
- Track error rates and set up alerts
- Understand traffic patterns

### 2. Business Metrics Dashboard
**File:** `grafana-business-metrics-dashboard.json`

**Metrics:**
- **Total Articles**: Count of all articles in database
- **Embedding Coverage**: Percentage of articles with embeddings
- **Sentiment Analysis**: Distribution of bullish/bearish/neutral sentiment
- **Source Distribution**: Articles by news source
- **Growth Over Time**: Articles, embeddings, and sentiment trends
- **Top Tokens**: Most mentioned cryptocurrencies
- **Confidence Scores**: Average confidence by sentiment category
- **Recent Activity**: Latest articles added (24h)

**Use Cases:**
- Track data ingestion and processing
- Monitor embedding generation progress
- Analyze sentiment distribution across sources
- Identify trending tokens and topics

## Setup Instructions

### Option 1: Import via Grafana Cloud UI (Recommended)

1. **Log in to Grafana Cloud**
   ```
   https://your-instance.grafana.net/
   ```

2. **Navigate to Dashboards**
   - Click "Dashboards" in the left sidebar
   - Click "New" → "Import"

3. **Import API Performance Dashboard**
   - Copy the contents of `grafana-api-performance-dashboard.json`
   - Paste into the "Import via panel json" field
   - Click "Load"
   - Select your Prometheus data source
   - Click "Import"

4. **Import Business Metrics Dashboard**
   - Repeat the same steps with `grafana-business-metrics-dashboard.json`

5. **Verify Data**
   - Check that panels are loading data
   - If panels show "No data", verify:
     - Prometheus is scraping metrics from `/metrics` endpoint
     - The crypto-agent service is running
     - Firewall rules allow Prometheus → crypto-agent connection

### Option 2: Import via Grafana API

```bash
# Set your Grafana Cloud credentials
export GRAFANA_URL="https://your-instance.grafana.net"
export GRAFANA_API_KEY="your-api-key-here"

# Import API Performance Dashboard
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @observability/grafana-api-performance-dashboard.json \
  "$GRAFANA_URL/api/dashboards/db"

# Import Business Metrics Dashboard
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @observability/grafana-business-metrics-dashboard.json \
  "$GRAFANA_URL/api/dashboards/db"
```

### Option 3: Import via Terraform (For Production)

If using Terraform for infrastructure:

```hcl
resource "grafana_dashboard" "api_performance" {
  config_json = file("${path.module}/observability/grafana-api-performance-dashboard.json")
}

resource "grafana_dashboard" "business_metrics" {
  config_json = file("${path.module}/observability/grafana-business-metrics-dashboard.json")
}
```

## Data Source Configuration

Both dashboards expect a Prometheus data source named "Prometheus" (default).

**To configure:**
1. Go to "Configuration" → "Data Sources" in Grafana
2. Add "Prometheus" data source
3. Set URL to your Prometheus instance (e.g., `http://prometheus:9090` for local)
4. For Grafana Cloud with remote_write, this is automatically configured

## Alerts Configuration

The API Performance Dashboard includes a pre-configured alert:

**High Error Rate Alert**
- Condition: Error rate > 5% for 5 minutes
- Notification: Configure via "Alerting" → "Notification channels"

**To add Slack notifications:**
1. Go to "Alerting" → "Notification channels"
2. Add new channel → Select "Slack"
3. Enter webhook URL or Slack API token
4. Test the notification
5. Save and link to the alert

## Troubleshooting

### No Data in Panels

**Problem:** Panels show "No data" or "N/A"

**Solutions:**
1. Verify Prometheus is scraping:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```
   Look for `crypto-agent:8000` target with status "UP"

2. Check metrics are being exposed:
   ```bash
   curl http://localhost:8000/metrics
   ```
   Should return Prometheus-formatted metrics

3. Verify remote_write is configured (if using Grafana Cloud):
   ```bash
   # Check prometheus.yml
   cat observability/prometheus.yml
   ```

### Metrics Not Updating

**Problem:** Metrics are stale or not refreshing

**Solutions:**
1. Check Prometheus scrape interval (default: 10-15s)
2. Verify the crypto-agent container is healthy:
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```
3. Restart Prometheus:
   ```bash
   docker compose restart prometheus
   ```

### Dashboard Variables Not Working

**Problem:** Template variables show no options

**Solutions:**
1. Verify the query syntax matches your Prometheus labels
2. Check that metrics have the expected labels (method, endpoint, status, etc.)
3. Refresh the dashboard or browser cache

## Customization

### Adding Custom Panels

1. Click "Add panel" in dashboard edit mode
2. Select "Add a new panel"
3. Choose visualization type (graph, stat, table, etc.)
4. Write PromQL query, e.g.:
   ```promql
   # Average embedding generation time
   histogram_quantile(0.95,
     rate(http_request_duration_seconds_bucket{endpoint="/api/embeddings/generate/"}[5m])
   )
   ```
5. Configure display options
6. Save the panel and dashboard

### Modifying Queries

All queries use PromQL (Prometheus Query Language). Common patterns:

```promql
# Rate of requests
rate(http_requests_total[5m])

# Aggregations
sum by (endpoint) (rate(http_requests_total[5m]))

# Percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Filtering
http_requests_total{status="200", method="GET"}
```

## Best Practices

1. **Set up alerts for critical metrics**
   - Error rate > 5%
   - p95 latency > 2s
   - Success rate < 95%

2. **Use dashboard folders**
   - Organize dashboards by team or service
   - Share folders with appropriate access levels

3. **Create dashboard snapshots**
   - For incident post-mortems
   - To share with stakeholders

4. **Use dashboard variables**
   - Filter by environment (dev, staging, prod)
   - Select specific endpoints or time ranges

5. **Document dashboard usage**
   - Add text panels with explanations
   - Link to runbooks for common issues

## For Students (Bootcamp)

During the bootcamp, use these dashboards to:

1. **Monitor your API** as you add new features
2. **Identify performance bottlenecks** in real-time
3. **Track embedding generation progress**
4. **Visualize sentiment analysis results**
5. **Learn PromQL** by modifying queries
6. **Practice incident response** by intentionally breaking things

### Exercise Ideas

- Set up a Slack alert for high error rates
- Create a custom panel showing semantic search latency
- Build a heatmap of requests by hour of day
- Track your embedding coverage going from 0% → 100%

## Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)
- [Grafana Cloud Free Tier](https://grafana.com/pricing/) - 10K series, 50GB logs/month

## Support

If you encounter issues:
1. Check the [Grafana Community Forums](https://community.grafana.com/)
2. Review the [Prometheus documentation](https://prometheus.io/docs/)
3. Ask in the bootcamp Slack channel
4. Open a GitHub issue with dashboard export and error logs

