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
      - AWS_REGION=\${AWS_REGION:-us-east-1}
      - S3_BUCKET_NAME=\${S3_BUCKET_NAME}
      - BEDROCK_MODEL_ID=\${BEDROCK_MODEL_ID:-anthropic.claude-3-haiku-20240307-v1:0}
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
EOF

# Start the application
echo "🚀 Starting application..."
docker-compose up -d

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
sleep 30

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