#!/bin/bash
# scripts/setup-github-actions.sh - Setup script for GitHub Actions

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 GitHub Actions Setup Script${NC}"
echo "=================================="

# Get user input
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your repository name: " REPO_NAME
read -p "Enter your EC2 public IP: " EC2_HOST
read -p "Enter path to your SSH private key: " SSH_KEY_PATH

# Validate inputs
if [ -z "$GITHUB_USERNAME" ] || [ -z "$REPO_NAME" ] || [ -z "$EC2_HOST" ] || [ -z "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ All fields are required!${NC}"
    exit 1
fi

if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key not found at: $SSH_KEY_PATH${NC}"
    exit 1
fi

# Get AWS account ID
echo -e "${YELLOW}📋 Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/GitHubActionsRole"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "GitHub Username: $GITHUB_USERNAME"
echo "Repository Name: $REPO_NAME"
echo "EC2 Host: $EC2_HOST"

# Create trust policy
echo -e "${YELLOW}📝 Creating trust policy...${NC}"
cat > github-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_USERNAME}/${REPO_NAME}:*"
        }
      }
    }
  ]
}
EOF

# Create OIDC provider (if not exists)
echo -e "${YELLOW}🔐 Creating OIDC identity provider...${NC}"
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --client-id-list sts.amazonaws.com \
  2>/dev/null || echo "OIDC provider already exists"

# Create IAM role
echo -e "${YELLOW}👤 Creating IAM role...${NC}"
aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://github-trust-policy.json \
  2>/dev/null || echo "Role already exists, updating trust policy..."

aws iam update-assume-role-policy \
  --role-name GitHubActionsRole \
  --policy-document file://github-trust-policy.json

# Attach policies
echo -e "${YELLOW}📋 Attaching policies...${NC}"
aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess

# Get SSH key content
echo -e "${YELLOW}🔑 Reading SSH key...${NC}"
SSH_KEY_CONTENT=$(cat "$SSH_KEY_PATH")

# Clean up
rm -f github-trust-policy.json

# Display GitHub secrets
echo -e "${GREEN}✅ IAM role created successfully!${NC}"
echo ""
echo -e "${BLUE}📋 GitHub Secrets to Add:${NC}"
echo "Go to: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/settings/secrets/actions"
echo ""
echo -e "${YELLOW}Add these secrets:${NC}"
echo ""
echo "Name: AWS_ROLE_ARN"
echo "Value: ${ROLE_ARN}"
echo ""
echo "Name: EC2_HOST"
echo "Value: ${EC2_HOST}"
echo ""
echo "Name: EC2_USER"
echo "Value: ubuntu"
echo ""
echo "Name: EC2_SSH_KEY"
echo "Value: (see below)"
echo ""
echo -e "${RED}SSH_KEY_CONTENT:${NC}"
echo "----------------------------------------"
echo "$SSH_KEY_CONTENT"
echo "----------------------------------------"
echo ""
echo "Name: CLOUDFRONT_DOMAIN"
echo "Value: your-cloudfront-domain.cloudfront.net"
echo ""
echo -e "${GREEN}🎉 Setup complete! Add these secrets to GitHub and push to main branch.${NC}"
