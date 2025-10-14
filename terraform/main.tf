# terraform/main.tf - Crypto Sentiment Agent Infrastructure
# Complete infrastructure for 5-day bootcamp (Days 1-4 implemented)

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================================
# Variables
# ============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "crypto-agent"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "key_pair_name" {
  description = "Name of existing EC2 Key Pair for SSH access"
  type        = string
}

variable "additional_ssh_ips" {
  description = "Additional IP addresses for SSH access (e.g., traveling, team members)"
  type        = list(string)
  default     = []
}

variable "github_repo" {
  description = "GitHub repository in format 'username/repo' for OIDC"
  type        = string
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets (increases cost)"
  type        = bool
  default     = false
}

# ============================================================================
# Data Sources
# ============================================================================

# Get current IP for SSH access
data "http" "my_ip" {
  url = "https://ipinfo.io/ip"
}

# Get latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get AWS account ID for IAM policies
data "aws_caller_identity" "current" {}

# ============================================================================
# VPC and Networking (using default VPC for simplicity)
# ============================================================================

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ============================================================================
# Security Groups
# ============================================================================

resource "aws_security_group" "crypto_agent" {
  name_prefix = "${var.project_name}-"
  description = "Security group for crypto sentiment agent EC2 instance"
  vpc_id      = data.aws_vpc.default.id

  # SSH access (current IP + additional IPs)
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = concat(
      ["${chomp(data.http.my_ip.response_body)}/32"],
      var.additional_ssh_ips
    )
  }

  # HTTP access (for testing without load balancer)
  ingress {
    description = "HTTP access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access (future use)
  ingress {
    description = "HTTPS access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI application port
  ingress {
    description = "FastAPI application"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus (optional, for local monitoring)
  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = concat(
      ["${chomp(data.http.my_ip.response_body)}/32"],
      var.additional_ssh_ips
    )
  }

  # Jaeger UI (optional, for local tracing)
  ingress {
    description = "Jaeger UI"
    from_port   = 16686
    to_port     = 16686
    protocol    = "tcp"
    cidr_blocks = concat(
      ["${chomp(data.http.my_ip.response_body)}/32"],
      var.additional_ssh_ips
    )
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-sg"
    Environment = var.environment
    Project     = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# IAM Roles and Policies
# ============================================================================

# IAM Role for EC2 Instance
resource "aws_iam_role" "ec2_instance" {
  name_prefix = "${var.project_name}-ec2-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ec2-role"
    Environment = var.environment
  }
}

# IAM Policy for EC2 - ECR Access
resource "aws_iam_role_policy" "ec2_ecr_access" {
  name_prefix = "${var.project_name}-ecr-"
  role        = aws_iam_role.ec2_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Policy for EC2 - S3 Access
resource "aws_iam_role_policy" "ec2_s3_access" {
  name_prefix = "${var.project_name}-s3-"
  role        = aws_iam_role.ec2_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::crypto-news-pdfs-sep-2025",
          "arn:aws:s3:::crypto-news-pdfs-sep-2025/*",
          "arn:aws:s3:::*crypto-agent*",
          "arn:aws:s3:::*crypto-agent*/*"
        ]
      }
    ]
  })
}

# IAM Policy for EC2 - Bedrock Access
resource "aws_iam_role_policy" "ec2_bedrock_access" {
  name_prefix = "${var.project_name}-bedrock-"
  role        = aws_iam_role.ec2_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ApplyGuardrail",
          "bedrock:GetGuardrail"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:guardrail/*"
      }
    ]
  })
}

# IAM Policy for EC2 - CloudWatch Logs (for observability)
resource "aws_iam_role_policy" "ec2_cloudwatch_logs" {
  name_prefix = "${var.project_name}-logs-"
  role        = aws_iam_role.ec2_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/ec2/${var.project_name}*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_instance" {
  name_prefix = "${var.project_name}-"
  role        = aws_iam_role.ec2_instance.name

  tags = {
    Name        = "${var.project_name}-instance-profile"
    Environment = var.environment
  }
}

# ============================================================================
# OIDC Provider for GitHub Actions
# ============================================================================

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "${var.project_name}-github-oidc"
    Environment = var.environment
  }
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name_prefix = "${var.project_name}-github-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-github-actions-role"
    Environment = var.environment
  }
}

# IAM Policy for GitHub Actions - ECR Push
resource "aws_iam_role_policy" "github_actions_ecr" {
  name_prefix = "${var.project_name}-ecr-push-"
  role        = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# EC2 Instance
# ============================================================================

resource "aws_instance" "crypto_agent" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.medium" # 2 vCPU, 4GB RAM - sufficient for pgvector
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.crypto_agent.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_instance.name

  # Storage - sufficient for Docker images, PostgreSQL, and logs
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  # User data script to install Docker and dependencies
  user_data = file("${path.module}/user_data.sh")

  # Enable detailed monitoring (additional cost)
  monitoring = false

  tags = {
    Name        = "${var.project_name}-ec2"
    Environment = var.environment
    Project     = var.project_name
    Terraform   = "true"
  }

  lifecycle {
    ignore_changes = [
      ami,
      user_data
    ]
  }
}

# ============================================================================
# Amazon ECR Repository
# ============================================================================

resource "aws_ecr_repository" "crypto_agent" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-ecr"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECR Lifecycle Policy - keep last 10 images
resource "aws_ecr_lifecycle_policy" "crypto_agent" {
  repository = aws_ecr_repository.crypto_agent.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ============================================================================
# CloudWatch Log Groups (for observability)
# ============================================================================

resource "aws_cloudwatch_log_group" "crypto_agent" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# Outputs
# ============================================================================

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.crypto_agent.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.crypto_agent.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.crypto_agent.public_dns
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.crypto_agent.repository_url
}

output "ecr_repository_arn" {
  description = "ECR repository ARN"
  value       = aws_ecr_repository.crypto_agent.arn
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.crypto_agent.id
}

output "iam_instance_profile_arn" {
  description = "IAM instance profile ARN"
  value       = aws_iam_instance_profile.ec2_instance.arn
}

output "github_actions_role_arn" {
  description = "GitHub Actions IAM role ARN (for OIDC)"
  value       = aws_iam_role.github_actions.arn
}

output "application_url" {
  description = "Application URL"
  value       = "http://${aws_instance.crypto_agent.public_ip}:8000"
}

output "health_check_url" {
  description = "Health check URL"
  value       = "http://${aws_instance.crypto_agent.public_ip}:8000/health"
}

output "prometheus_url" {
  description = "Prometheus URL (if accessible)"
  value       = "http://${aws_instance.crypto_agent.public_ip}:9090"
}

output "jaeger_url" {
  description = "Jaeger UI URL (if accessible)"
  value       = "http://${aws_instance.crypto_agent.public_ip}:16686"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.crypto_agent.public_ip}"
}

# ============================================================================
# Additional Notes for Students
# ============================================================================

# This Terraform configuration creates:
# 1. EC2 instance (t3.medium) with Ubuntu 22.04 LTS
# 2. Security group allowing HTTP/HTTPS/SSH/Custom ports
# 3. IAM role for EC2 with permissions for ECR, S3, Bedrock, CloudWatch
# 4. ECR repository for Docker images
# 5. OIDC provider for GitHub Actions (secure, no credentials needed)
# 6. IAM role for GitHub Actions with ECR push permissions
# 7. CloudWatch log group for application logs
#
# Prerequisites:
# - AWS account with sufficient permissions
# - Existing EC2 Key Pair for SSH access
# - GitHub repository for OIDC configuration
#
# Usage:
# 1. Copy terraform.tfvars.example to terraform.tfvars
# 2. Fill in your values (key_pair_name, github_repo)
# 3. Run: terraform init
# 4. Run: terraform plan
# 5. Run: terraform apply
#
# Cost Estimate (24/7):
# - EC2 t3.medium: ~$30/month
# - EBS 30GB gp3: ~$2.40/month
# - ECR storage: ~$0.10/month (first 500MB free)
# - CloudWatch Logs: Free tier (5GB)
# - Total: ~$32-35/month
#
# For Day 4 (Guardrails), you'll need to:
# - Enable Bedrock Guardrails in AWS Console
# - Add guardrail configuration
# - Update IAM policy with guardrail permissions (already included above)
