#!/bin/bash
# terraform/user_data.sh - EC2 Instance Setup Script

set -e  # Exit on any error

echo "🚀 Starting EC2 instance setup..."

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
echo "📦 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
echo "📦 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
echo "📦 Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Install Git
echo "📦 Installing Git..."
apt-get install -y git

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/crypto-agent
cd /opt/crypto-agent

# Create environment file template
echo "📝 Creating environment file..."
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://crypto:crypToCurDBpass2025!@localhost:5432/crypto_news
POSTGRES_DB=crypto_news
POSTGRES_USER=crypto
POSTGRES_PASSWORD=crypToCurDBpass2025!

# AWS Configuration (will be set via SSM Parameter Store)
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# CoinGecko API
COINGECKO_API_KEY=your-api-key

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Create systemd service for the application
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/crypto-agent.service << EOF
[Unit]
Description=Crypto Sentiment Agent
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/crypto-agent
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl enable crypto-agent.service

# Create health check script
echo "🏥 Creating health check script..."
cat > /opt/crypto-agent/health-check.sh << 'EOF'
#!/bin/bash
# Health check script

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check if application container is running
if ! docker ps | grep -q crypto-agent; then
    echo "❌ Application container is not running"
    exit 1
fi

# Check if application responds
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Application health check failed"
    exit 1
fi

echo "✅ All health checks passed"
exit 0
EOF

chmod +x /opt/crypto-agent/health-check.sh

# Create log rotation
echo "📋 Setting up log rotation..."
cat > /etc/logrotate.d/crypto-agent << EOF
/opt/crypto-agent/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
EOF

# Set proper permissions
chown -R ubuntu:ubuntu /opt/crypto-agent

echo "✅ EC2 instance setup completed!"
echo "📋 Next steps:"
echo "   1. SSH into the instance"
echo "   2. Copy your application code to /opt/crypto-agent"
echo "   3. Update the .env file with your actual values"
echo "   4. Run: docker-compose up -d"

# Signal completion
echo "Setup completed at $(date)" > /var/log/crypto-agent-setup.log
