# terraform/main.tf - Complete Infrastructure from Scratch
terraform {
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

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "additional_ssh_ips" {
  description = "Additional IPs for SSH access (for traveling)"
  type        = list(string)
  default     = []
}

variable "key_pair_name" {
  description = "Name of your existing EC2 Key Pair"
  type        = string
  default     = ""
}

# Data source for CloudFront IP ranges
data "aws_ip_ranges" "cloudfront" {
  regions  = ["global"]
  services = ["cloudfront"]
}

# Get your current IP
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

# Security Group
resource "aws_security_group" "crypto_agent" {
  name_prefix = "crypto-agent-"
  description = "Security group for crypto sentiment agent"

  # SSH access (your current IP + additional IPs)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = concat(
      ["${chomp(data.http.my_ip.response_body)}/32"],
      var.additional_ssh_ips
    )
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
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"  # 2 vCPU, 4GB RAM

  vpc_security_group_ids = [aws_security_group.crypto_agent.id]

  # Use your existing key pair if provided
  key_name = var.key_pair_name != "" ? var.key_pair_name : null

  # Storage
  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  # User data script to install Docker and setup
  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name        = "crypto-sentiment-agent"
    Environment = "production"
    Project     = "crypto-agent"
  }
}

# ECR Repository
resource "aws_ecr_repository" "crypto_agent" {
  name                 = "crypto-sentiment-agent"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "crypto-agent-ecr"
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

# Outputs
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.crypto_agent.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.crypto_agent.public_dns
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.crypto_agent.domain_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.crypto_agent.repository_url
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.crypto_agent.id
}
