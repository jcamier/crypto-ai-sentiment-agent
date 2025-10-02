#!/bin/bash
# terraform/setup.sh - Quick setup script for fresh Terraform deployment

echo "🚀 Setting up Terraform for a fresh EC2 instance deployment..."

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first:"
    echo "   https://developer.hashicorp.com/terraform/downloads"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

# Get current IP
echo "📍 Getting your current IP address..."
CURRENT_IP=$(curl -s https://ipinfo.io/ip)
echo "   Your IP: $CURRENT_IP"

# Check for existing key pairs
echo "🔑 Checking for existing EC2 Key Pairs..."
aws ec2 describe-key-pairs \
  --query 'KeyPairs[*].[KeyName,KeyFingerprint]' \
  --output table

echo ""
echo "📝 Setup steps:"
echo "   1. Copy terraform.tfvars.example to terraform.tfvars:"
echo "      cp terraform.tfvars.example terraform.tfvars"
echo ""
echo "   2. Edit terraform.tfvars (optional):"
echo "      - Add your key pair name if you have one"
echo "      - Add additional IPs for SSH access"
echo ""
echo "   3. Initialize and deploy:"
echo "      terraform init"
echo "      terraform plan    # Review what will be created"
echo "      terraform apply   # Create everything"
echo ""
echo "   4. After deployment:"
echo "      - SSH into your new instance"
echo "      - Copy your application code"
echo "      - Update environment variables"
echo "      - Start your application"
echo ""
echo "💡 This will create:"
echo "   - EC2 instance (t3.small, Ubuntu 22.04)"
echo "   - Security group with proper rules"
echo "   - ECR repository for Docker images"
echo "   - CloudFront distribution"
echo "   - All properly configured and ready to use!"
