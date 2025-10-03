#!/bin/bash
# scripts/manual-deploy.sh - Manual deployment script

set -e  # Exit on any error

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="crypto-sentiment-agent"
EC2_HOST=""  # Set this to your EC2 public IP
EC2_USER="ubuntu"
SSH_KEY_PATH=""  # Set this to your SSH key path

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Manual Deployment Script for Crypto Agent${NC}"
echo "================================================"

# Check if required variables are set
if [ -z "$EC2_HOST" ] || [ -z "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ Please set EC2_HOST and SSH_KEY_PATH variables in this script${NC}"
    echo "Edit this file and set:"
    echo "  EC2_HOST=\"your-ec2-public-ip\""
    echo "  SSH_KEY_PATH=\"path/to/your/key.pem\""
    exit 1
fi

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key not found at: $SSH_KEY_PATH${NC}"
    exit 1
fi

# Get AWS account ID
echo -e "${YELLOW}📋 Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
ECR_IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:latest"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR Registry: $ECR_REGISTRY"
echo "EC2 Host: $EC2_HOST"

# Build and push Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t $ECR_REPOSITORY:latest .

echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker tag $ECR_REPOSITORY:latest $ECR_IMAGE
docker push $ECR_IMAGE

# Copy application files to EC2
echo -e "${YELLOW}📁 Copying application files to EC2...${NC}"
scp -i $SSH_KEY_PATH -o StrictHostKeyChecking=no -r . $EC2_USER@$EC2_HOST:/opt/crypto-agent/

# Copy and run deployment script on EC2
echo -e "${YELLOW}🚀 Running deployment on EC2...${NC}"
ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST "
    cd /opt/crypto-agent
    chmod +x scripts/deploy.sh
    ./scripts/deploy.sh $ECR_IMAGE
"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your application is running at: http://$EC2_HOST:8000${NC}"
echo -e "${GREEN}🏥 Health check: http://$EC2_HOST:8000/health${NC}"
