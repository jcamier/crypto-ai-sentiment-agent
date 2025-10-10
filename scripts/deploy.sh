#!/bin/bash
# scripts/deploy.sh - Deployment script for EC2 instance

set -e  # Exit on any error

# Get the image name from command line argument
IMAGE_NAME=${1:-"crypto-sentiment-agent:latest"}

echo "🚀 Starting deployment of $IMAGE_NAME..."

# Install Docker and AWS CLI if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo usermod -aG docker ubuntu
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "⚠️  Docker installed. You may need to log out and back in for permissions to take effect."
fi

# Ensure ubuntu user is in docker group and restart docker if needed
if ! groups ubuntu | grep -q docker; then
    echo "📦 Adding ubuntu user to docker group..."
    sudo usermod -aG docker ubuntu
    sudo systemctl restart docker
fi

# Test docker permissions
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker permission issue detected. Trying to fix..."
    sudo chmod 666 /var/run/docker.sock
    sudo systemctl restart docker
fi

if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    sudo apt install -y awscli
fi

# Create application directory if it doesn't exist
mkdir -p /opt/crypto-agent
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
      - BEDROCK_MODEL_ID=\${BEDROCK_MODEL_ID}
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
echo "📝 Creating .env file from environment variables..."
cat > .env << EOF
# Database Configuration
DB_NAME=${DB_NAME:-crypto_news}
DB_USER=${DB_USER:-crypto}
DB_PASS=${DB_PASS}

# AWS Configuration
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REGION=${AWS_REGION:-us-east-1}
S3_BUCKET_NAME=${S3_BUCKET_NAME}
BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-anthropic.claude-3-sonnet-20240229-v1:0}

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