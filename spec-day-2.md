# Crypto News & Sentiment Agent - Day 2 Specification

## Project Overview
Build AWS infrastructure and CI/CD pipeline for the crypto news sentiment agent, deploying it to production-ready AWS environment with automated deployment workflows.

## Why This Approach?
Day 2 focuses on **production infrastructure** and **DevOps practices** that are essential for any real-world AI application:

### Enterprise Infrastructure
- **AWS EC2**: Learn to deploy containerized applications on cloud infrastructure
- **Amazon ECR**: Master container registry management for production deployments
- **IAM Roles**: Understand least-privilege security principles
- **SSM Parameter Store**: Learn secure secrets management patterns

### CI/CD Pipeline
- **GitHub Actions**: Build automated deployment workflows
- **OIDC Authentication**: Modern, secure authentication without storing secrets
- **Infrastructure as Code**: Use Terraform for reproducible infrastructure
- **Automated Testing**: Integrate tests into deployment pipeline

### Production Readiness
- **Container Registry**: Store and version Docker images properly
- **Secrets Management**: Secure handling of API keys and credentials
- **Health Checks**: Monitor application health in production
- **Rollback Capabilities**: Safe deployment practices

## Prerequisites: AWS Account Setup

**⚠️ IMPORTANT: Complete AWS account setup before proceeding**

### Required AWS Resources:
1. **AWS Account** with billing enabled and sufficient credits
2. **IAM User** with programmatic access and admin permissions (for initial setup)
3. **EC2 Instance** (t3.small - 2 vCPU, 2GB RAM, cost-effective)
4. **ECR Repository** for storing Docker images
5. **SSM Parameter Store** for secrets management

### IAM Permissions:
Create IAM roles with the following policies:
- **EC2 Instance Role**: ECR access, SSM Parameter Store access
- **GitHub Actions Role**: ECR push/pull, EC2 deployment, SSM access
- **OIDC Identity Provider**: For GitHub Actions authentication

### Setup Steps:
1. Create IAM user with admin permissions (for initial setup)
2. Generate Access Key ID and Secret Access Key
3. Create ECR repository for crypto-agent images
4. Set up SSM Parameter Store for secrets
5. Configure GitHub repository with OIDC authentication
6. Test AWS connectivity and permissions

**Note**: Without proper AWS setup, the deployment pipeline will fail.

## Day 2 Requirements

### Core Infrastructure
- **EC2 Instance**: Deploy crypto-agent to AWS EC2 (t4g.large)
- **ECR Repository**: Store Docker images in Amazon ECR
- **SSM Parameter Store**: Store API keys and secrets securely
- **IAM Roles**: Implement least-privilege access patterns
- **Security Groups**: Configure network access controls

### CI/CD Pipeline
- **GitHub Actions**: Automated build and deployment workflow
- **OIDC Authentication**: Secure AWS authentication without secrets
- **Terraform**: Infrastructure as Code for reproducible deployments
- **Docker Build**: Automated image building and pushing to ECR
- **Health Checks**: Automated deployment verification

### Technical Stack
- **Cloud Provider**: AWS (EC2, ECR, IAM, SSM)
- **CI/CD**: GitHub Actions with OIDC
- **Infrastructure**: Terraform for AWS resources
- **Container Registry**: Amazon ECR
- **Secrets Management**: AWS SSM Parameter Store
- **Monitoring**: Basic health checks and logging

### Infrastructure Components

#### Architecture Overview
```
Internet → CloudFront → EC2 (FastAPI + PostgreSQL)
                ↓
            ECR (Docker Images)
                ↓
            GitHub Actions (CI/CD)
```

#### EC2 Instance Configuration
```yaml
Instance Type: t3.small (2 vCPU, 2GB RAM - perfect for pgvector)
AMI: Ubuntu Server 22.04 LTS
Storage: 20GB GP3
Security Groups: See detailed configuration below
```

#### Security Group Configuration
```yaml
Security Group Name: crypto-agent-sg
Description: Security group for crypto sentiment agent

Inbound Rules:
  - SSH (22): Multiple IPs (for traveling and team access)
  - HTTP (80): CloudFront IPs only (for CloudFront distribution)
  - HTTPS (443): CloudFront IPs only (for secure CloudFront access)
  - Custom (8000): CloudFront IPs only (for API access via CloudFront)
  - Custom (5432): 127.0.0.1/32 (PostgreSQL - localhost only)

Outbound Rules:
  - All Traffic: 0.0.0.0/0 (for API calls to AWS, CoinGecko, etc.)

Note: CloudFront IPs are dynamic - use CloudFront service for IP ranges
```

#### ECR Repository Setup
```bash
Repository Name: crypto-sentiment-agent
Image Tags: latest, v1.0.0, commit-sha
Lifecycle Policy: Keep last 10 images
Encryption: AES-256
```

#### SSM Parameter Store Structure
```bash
/crypto-agent/database/url
/crypto-agent/aws/access-key-id
/crypto-agent/aws/secret-access-key
/crypto-agent/coingecko/api-key
/crypto-agent/s3/bucket-name
/crypto-agent/bedrock/model-id
```

### GitHub Actions CI/CD

#### Workflow Configuration
```yaml
# .github/workflows/deploy.yml
name: Deploy Crypto Agent

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ -v
      - name: Run linting
        run: |
          flake8 src/ tests/
          black --check src/ tests/

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: crypto-sentiment-agent
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Deploy to EC2
        env:
          EC2_HOST: ${{ secrets.EC2_HOST }}
          EC2_USER: ${{ secrets.EC2_USER }}
        run: |
          echo "${{ secrets.EC2_SSH_KEY }}" > ssh_key
          chmod 600 ssh_key
          ssh -i ssh_key -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST '
            aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
            docker pull $ECR_REGISTRY/$ECR_REPOSITORY:latest
            docker stop crypto-agent || true
            docker rm crypto-agent || true
            docker run -d --name crypto-agent -p 8000:8000 --env-file /opt/crypto-agent/.env $ECR_REGISTRY/$ECR_REPOSITORY:latest
          '

      - name: Health Check
        run: |
          sleep 30
          curl -f https://${{ secrets.CLOUDFRONT_DOMAIN }}/health || exit 1
```

#### Required GitHub Secrets
```yaml
AWS_ROLE_ARN: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
EC2_HOST: your-ec2-public-ip
EC2_USER: ubuntu
EC2_SSH_KEY: your-private-ssh-key
CLOUDFRONT_DOMAIN: your-cloudfront-domain.cloudfront.net
```

### SSH Access Management

#### Multiple IP Support for Traveling
```bash
# Get your current IP
curl -s https://ipinfo.io/ip

# Update security group with new IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_NEW_IP/32

# Remove old IP when leaving location
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_OLD_IP/32
```

#### Recommended IP Management Strategy
1. **Home IP**: Always allowed (static)
2. **Office IP**: Always allowed (static)
3. **VPN IP**: Optional, for secure connections
4. **Travel IPs**: Add/remove as needed
5. **Team IPs**: Add for collaboration

#### Automated IP Management Script
```bash
#!/bin/bash
# update-ssh-access.sh
CURRENT_IP=$(curl -s https://ipinfo.io/ip)
SECURITY_GROUP_ID="sg-xxxxxxxxx"

echo "Current IP: $CURRENT_IP"

# Add current IP to security group
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 22 \
  --cidr ${CURRENT_IP}/32

echo "Added $CURRENT_IP to security group"
```

### Terraform Infrastructure

#### Main Components
```hcl
# Data source for CloudFront IP ranges
data "aws_ip_ranges" "cloudfront" {
  regions  = ["global"]
  services = ["cloudfront"]
}

# Security Group
resource "aws_security_group" "crypto_agent" {
  name_prefix = "crypto-agent-"
  description = "Security group for crypto sentiment agent"

  # SSH access (multiple IPs for traveling)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [
      "YOUR_HOME_IP/32",      # Replace with your home IP
      "YOUR_OFFICE_IP/32",    # Replace with your office IP
      "YOUR_VPN_IP/32"        # Replace with your VPN IP (optional)
    ]
  }

  # HTTP access (CloudFront only)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = data.aws_ip_ranges.cloudfront.cidr_blocks
  }

  # HTTPS access (CloudFront only)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = data.aws_ip_ranges.cloudfront.cidr_blocks
  }

  # Application port (CloudFront only)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = data.aws_ip_ranges.cloudfront.cidr_blocks
  }

  # PostgreSQL (localhost only)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["127.0.0.1/32"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "crypto-agent-sg"
  }
}

# EC2 Instance
resource "aws_instance" "crypto_agent" {
  ami           = "ami-0c7217cde4661b399"  # Ubuntu Server 22.04 LTS
  instance_type = "t3.small"  # 2 vCPU, 2GB RAM

  vpc_security_group_ids = [aws_security_group.crypto_agent.id]
  iam_instance_profile   = aws_iam_instance_profile.crypto_agent.name

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name = "crypto-sentiment-agent"
    Environment = "production"
  }
}

# ECR Repository
resource "aws_ecr_repository" "crypto_agent" {
  name                 = "crypto-sentiment-agent"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "crypto_agent" {
  origin {
    domain_name = aws_instance.crypto_agent.public_dns
    origin_id   = "crypto-agent-origin"

    custom_origin_config {
      http_port              = 8000
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "health"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "crypto-agent-origin"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "crypto-agent-distribution"
  }
}

# SSM Parameters
resource "aws_ssm_parameter" "database_url" {
  name  = "/crypto-agent/database/url"
  type  = "SecureString"
  value = var.database_url
}
```

### Deployment Process

#### Initial Setup
1. **Terraform Apply**: Create AWS infrastructure
2. **ECR Login**: Configure Docker for ECR
3. **Build & Push**: Create and store Docker image
4. **SSM Setup**: Store secrets in Parameter Store
5. **EC2 Deployment**: Deploy application to EC2

#### Automated Deployment
1. **Code Push**: Developer pushes to main branch
2. **GitHub Actions**: Workflow triggers automatically
3. **Build Phase**: Create new Docker image
4. **Test Phase**: Run automated tests
5. **Deploy Phase**: Update EC2 instance
6. **Verify Phase**: Health check and validation

### Security Implementation

#### IAM Roles and Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/crypto-agent/*"
    }
  ]
}
```

#### OIDC Configuration
```yaml
# GitHub Actions OIDC Trust Policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:USERNAME/REPO:*"
        }
      }
    }
  ]
}
```

### Environment Configuration

#### Production Environment Variables
```bash
# Retrieved from SSM Parameter Store at runtime
DATABASE_URL=${SSM:/crypto-agent/database/url}
AWS_ACCESS_KEY_ID=${SSM:/crypto-agent/aws/access-key-id}
AWS_SECRET_ACCESS_KEY=${SSM:/crypto-agent/aws/secret-access-key}
COINGECKO_API_KEY=${SSM:/crypto-agent/coingecko/api-key}
S3_BUCKET_NAME=${SSM:/crypto-agent/s3/bucket-name}
BEDROCK_MODEL_ID=${SSM:/crypto-agent/bedrock/model-id}
```

#### Docker Compose for Production
```yaml
version: '3.8'
services:
  crypto-agent:
    image: ${ECR_REGISTRY}/crypto-sentiment-agent:${IMAGE_TAG}
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Success Criteria
- [ ] Successfully create AWS infrastructure with Terraform
- [ ] Set up ECR repository and push Docker images
- [ ] Configure SSM Parameter Store with all secrets
- [ ] Deploy application to EC2 instance
- [ ] Implement GitHub Actions CI/CD pipeline
- [ ] Configure OIDC authentication for GitHub Actions
- [ ] Verify automated deployment workflow
- [ ] Test health checks and monitoring
- [ ] Implement rollback capabilities
- [ ] Document deployment process

### Deliverables
- **Terraform Infrastructure**: Complete AWS resource definitions
- **GitHub Actions Workflow**: Automated CI/CD pipeline
- **ECR Repository**: Container registry with images
- **SSM Parameters**: Secure secrets management
- **EC2 Deployment**: Running production application
- **IAM Roles**: Least-privilege access policies
- **Security Groups**: Network access controls
- **Health Checks**: Application monitoring
- **Documentation**: Deployment and troubleshooting guides

### Cost Optimization
- **EC2 Instance**: Use t3.small ($0.0243/hr = ~$18/month for 24/7)
- **ECR Storage**: Implement lifecycle policies to manage image storage
- **SSM Parameters**: Use Standard parameters for non-sensitive data
- **Monitoring**: Basic CloudWatch metrics (free tier)
- **Estimated Monthly Cost**: $18-20 for development environment

### Troubleshooting Guide

#### Common Issues
1. **OIDC Authentication Failures**
   - Verify GitHub repository settings
   - Check IAM trust policy conditions
   - Ensure correct audience and subject claims

2. **ECR Push Failures**
   - Verify ECR repository exists
   - Check IAM permissions for ECR
   - Ensure Docker is logged into ECR

3. **EC2 Deployment Issues**
   - Verify security group rules
   - Check IAM instance profile
   - Validate user data script

4. **SSM Parameter Access**
   - Verify IAM permissions for SSM
   - Check parameter names and paths
   - Ensure correct region configuration

### Next Steps (Day 3 Preview)
- **Observability**: Add Prometheus + Grafana monitoring
- **Vector Database**: Implement pgvector for embeddings
- **Advanced Sentiment**: Enhanced sentiment analysis with embeddings
- **Performance**: Optimize for production workloads
- **Scaling**: Prepare for horizontal scaling

### Resources
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security/hardening-your-deployments)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWS SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
