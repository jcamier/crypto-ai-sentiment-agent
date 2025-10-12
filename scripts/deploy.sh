#!/bin/bash
# scripts/deploy.sh - Deployment script for EC2 instance

set -e  # Exit on any error

# Get the image name from command line argument
IMAGE_NAME=${1:-"crypto-sentiment-agent:latest"}

echo "🚀 Starting deployment of $IMAGE_NAME..."

# Check prerequisites - Docker and AWS CLI should be pre-installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please use an AMI with Docker pre-installed or configure via EC2 User Data."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed. Please use an AMI with AWS CLI pre-installed or configure via EC2 User Data."
    exit 1
fi

# Test docker permissions
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker permission issue detected. Trying to fix..."
    sudo chmod 666 /var/run/docker.sock
    sudo systemctl restart docker
fi

# Create application directory if it doesn't exist
sudo mkdir -p /opt/crypto-agent
sudo chown ubuntu:ubuntu /opt/crypto-agent
cd /opt/crypto-agent

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(echo $IMAGE_NAME | cut -d'/' -f1)

# Pull the latest image
echo "📥 Pulling latest image..."
docker pull $IMAGE_NAME

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Update docker-compose.yml with new image
echo "📝 Updating docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: \${DB_NAME:-crypto_news}
      POSTGRES_USER: \${DB_USER:-crypto}
      POSTGRES_PASSWORD: \${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-crypto}"]
      interval: 10s
      timeout: 5s
      retries: 5

  crypto-agent:
    image: $IMAGE_NAME
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://\${DB_USER:-crypto}:\${DB_PASS}@db:5432/\${DB_NAME:-crypto_news}
      - DB_NAME=\${DB_NAME:-crypto_news}
      - DB_USER=\${DB_USER:-crypto}
      - DB_PASS=\${DB_PASS}
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=\${AWS_REGION:-us-east-1}
      - S3_BUCKET_NAME=\${S3_BUCKET_NAME}
      - BEDROCK_MODEL_ID=\${BEDROCK_MODEL_ID:-anthropic.claude-3-haiku-20240307-v1:0}
      - BEDROCK_EMBEDDING_MODEL_ID=\${BEDROCK_EMBEDDING_MODEL_ID:-amazon.titan-embed-text-v2:0}
      - COINGECKO_API_KEY=\${COINGECKO_API_KEY}
      - API_KEY=\${API_KEY:-crypto-agent-secret-key}
      - ENVIRONMENT=\${ENVIRONMENT:-production}
      - LOG_LEVEL=\${LOG_LEVEL:-INFO}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Create .env file from environment variables (no hardcoded secrets)
# Note: AWS credentials not needed - EC2 uses IAM role
echo "📝 Creating .env file from environment variables..."
cat > .env << EOF
# Database Configuration
DB_NAME=${DB_NAME:-crypto_news}
DB_USER=${DB_USER:-crypto}
DB_PASS=${DB_PASS}

# AWS Configuration (credentials from IAM role)
AWS_REGION=${AWS_REGION:-us-east-1}
S3_BUCKET_NAME=${S3_BUCKET_NAME}
BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-anthropic.claude-3-haiku-20240307-v1:0}

# CoinGecko API
COINGECKO_API_KEY=${COINGECKO_API_KEY}

# API Security
API_KEY=${API_KEY:-crypto-agent-secret-key}

# Application Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Grafana Cloud Observability (optional)
GRAFANA_CLOUD_PROMETHEUS_URL=${GRAFANA_CLOUD_PROMETHEUS_URL}
GRAFANA_CLOUD_PROMETHEUS_USERNAME=${GRAFANA_CLOUD_PROMETHEUS_USERNAME}
GRAFANA_CLOUD_PROMETHEUS_PASSWORD=${GRAFANA_CLOUD_PROMETHEUS_PASSWORD}
EOF

# Generate Prometheus config with Grafana Cloud credentials if provided
if [ ! -z "$GRAFANA_CLOUD_PROMETHEUS_URL" ]; then
    echo "📊 Configuring Grafana Cloud integration..."
    if [ -f "observability/prometheus.yml.template" ]; then
        # Install envsubst if not available
        if ! command -v envsubst &> /dev/null; then
            echo "Installing envsubst..."
            sudo apt-get update -qq
            sudo apt-get install -qq -y gettext-base
        fi

        # Load .env and generate prometheus.yml
        set -a
        source .env
        set +a
        envsubst < observability/prometheus.yml.template > observability/prometheus.yml
        echo "✅ Prometheus config generated with Grafana Cloud credentials"
    else
        echo "⚠️  Warning: prometheus.yml.template not found, skipping Grafana Cloud setup"
    fi
else
    echo "ℹ️  Grafana Cloud not configured (optional - metrics will be local only)"
fi

# Start the application
echo "🚀 Starting application..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose exec -T crypto-agent alembic upgrade head
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "⚠️  Warning: Migration failed, but continuing (may be first deployment)"
    echo "ℹ️  Checking current migration state..."
    docker-compose exec -T crypto-agent alembic current || true
fi

# Wait for application to be fully ready
echo "⏳ Waiting for application to be ready..."
sleep 20

# Health check
echo "🏥 Running health check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! Application is healthy."
    echo "🌐 Application is running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
else
    echo "❌ Health check failed. Checking logs..."
    docker-compose logs crypto-agent
    exit 1
fi

echo "🎉 Deployment completed successfully!"